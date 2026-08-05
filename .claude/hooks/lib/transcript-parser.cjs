#!/usr/bin/env node
'use strict';

/**
 * Session transcript reader — extracts tool, agent, and task state from JSONL.
 * Called by hooks that need live session context (statusline, session-init).
 * No event firing; read-only extraction from the transcript file on disk.
 * @module transcript-parser
 */

const fs = require('fs');
const readline = require('readline');

function isNativeTaskTodo(todo) {
  return Boolean(todo && todo._source === 'native_task');
}

function normalizeTodo(todo) {
  if (!todo || typeof todo !== 'object') return null;
  const normalized = {
    content: todo.content ?? '',
    status: todo.status ?? 'pending',
    activeForm: todo.activeForm ?? null
  };
  if (todo.id != null) normalized.id = todo.id;
  return normalized;
}

function extractTaskIdFromString(text) {
  if (!text || typeof text !== 'string') return null;
  const trimmed = text.trim();
  if (!trimmed) return null;

  try {
    const parsed = JSON.parse(trimmed);
    return extractTaskIdFromValue(parsed);
  } catch {
    // Not JSON, continue with regex extraction.
  }

  const match = trimmed.match(/["']?task[_-]?id["']?\s*[:=]\s*["']([^"']+)["']/i);
  if (match && match[1]) return match[1];
  return null;
}

function extractTaskIdFromValue(value) {
  if (value == null) return null;

  if (typeof value === 'string') {
    return extractTaskIdFromString(value);
  }

  if (typeof value !== 'object') return null;

  if (typeof value.taskId === 'string' || typeof value.taskId === 'number') {
    return String(value.taskId);
  }
  if (typeof value.task_id === 'string' || typeof value.task_id === 'number') {
    return String(value.task_id);
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      const taskId = extractTaskIdFromValue(item);
      if (taskId) return taskId;
    }
    return null;
  }

  for (const fieldValue of Object.values(value)) {
    const taskId = extractTaskIdFromValue(fieldValue);
    if (taskId) return taskId;
  }
  return null;
}

/**
 * Stream-parse a session JSONL transcript and return aggregated state.
 * Returns a partial result on I/O error rather than throwing.
 * @param {string} transcriptPath - Absolute path to the JSONL transcript file
 * @returns {Promise<TranscriptData>}
 */
async function parseTranscript(transcriptPath) {
  const result = {
    tools: [],
    agents: [],
    todos: [],
    sessionStart: null,
    statuslineActivityCount: 0,
    invalidLineCount: 0,
    lastValidEntryAt: null,
    lastActivityAt: null
  };

  if (!transcriptPath || !fs.existsSync(transcriptPath)) {
    return result;
  }

  const toolMap = new Map();
  const agentMap = new Map();
  let latestTodos = [];

  try {
    const fileStream = fs.createReadStream(transcriptPath);
    const rl = readline.createInterface({
      input: fileStream,
      crlfDelay: Infinity
    });

    for await (const line of rl) {
      if (!line.trim()) continue;

      try {
        const entry = JSON.parse(line);
        processEntry(entry, toolMap, agentMap, latestTodos, result);
      } catch {
        result.invalidLineCount += 1;
      }
    }
  } catch {
    // Partial results are better than nothing — swallow stream errors here.
  }

  result.tools = Array.from(toolMap.values()).slice(-20);
  result.agents = Array.from(agentMap.values()).slice(-10);
  result.todos = latestTodos
    .map(normalizeTodo)
    .filter(Boolean);

  return result;
}

/**
 * Mutate tracking maps with data from one JSONL entry.
 * @param {Object} entry - Parsed JSON line from the transcript
 * @param {Map} toolMap - Running map of tool_use_id → tool state
 * @param {Map} agentMap - Running map of tool_use_id → agent state
 * @param {Array} latestTodos - Mutable task list, replaced on each TodoWrite
 * @param {Object} result - Accumulator mutated in place
 */
function processEntry(entry, toolMap, agentMap, latestTodos, result) {
  const parsedTimestamp = entry.timestamp ? new Date(entry.timestamp) : new Date();
  const timestamp = Number.isNaN(parsedTimestamp.getTime()) ? new Date() : parsedTimestamp;
  const timestampIso = timestamp.toISOString();
  let hadActivity = false;

  result.lastValidEntryAt = timestampIso;

  // Capture first timestamp as session start.
  if (!result.sessionStart && entry.timestamp) {
    result.sessionStart = timestamp;
  }

  const content = entry.message?.content;
  if (!content || !Array.isArray(content)) return;

  for (const block of content) {
    // tool_use: record spawns, task mutations, and regular tool calls.
    if (block.type === 'tool_use' && block.id && block.name) {
      if (block.name === 'Task') {
        result.statuslineActivityCount += 1;
        hadActivity = true;
        // Subagent spawn — tracked until its tool_result arrives.
        agentMap.set(block.id, {
          id: block.id,
          type: block.input?.subagent_type ?? 'unknown',
          model: block.input?.model ?? null,
          description: block.input?.description ?? null,
          status: 'running',
          startTime: timestamp,
          endTime: null
        });
      } else if (block.name === 'TodoWrite') {
        result.statuslineActivityCount += 1;
        hadActivity = true;
        // Legacy tool — replaces the full task array. Kept for backwards compatibility.
        if (block.input?.todos && Array.isArray(block.input.todos)) {
          latestTodos.length = 0;
          latestTodos.push(
            ...block.input.todos.map(todo => ({
              ...todo,
              _source: 'legacy_todowrite'
            }))
          );
        }
      } else if (block.name === 'TaskCreate') {
        result.statuslineActivityCount += 1;
        hadActivity = true;
        // Native Task API: new task. Keyed by tool_use id initially;
        // the real task id is hydrated from the matching tool_result.
        if (block.input?.subject) {
          latestTodos.push({
            id: block.id,
            content: block.input.subject,
            status: 'pending',
            activeForm: block.input.activeForm || null,
            _source: 'native_task',
            _toolUseId: block.id
          });
        }
      } else if (block.name === 'TaskUpdate') {
        result.statuslineActivityCount += 1;
        hadActivity = true;
        // Native Task API: update task status.
        // Match by taskId string first; numeric fallback resolves by creation order
        // within native tasks only — never against legacy TodoWrite items.
        if (block.input?.taskId && block.input?.status) {
          const taskId = String(block.input.taskId);
          const nativeTodos = latestTodos.filter(isNativeTaskTodo);
          let task = nativeTodos.find(t => String(t.id) === taskId);
          if (!task && /^\d+$/.test(taskId)) {
            const idx = Number(taskId) - 1;
            if (idx >= 0 && idx < nativeTodos.length) task = nativeTodos[idx];
          }

          if (task) {
            task.status = block.input.status;
            if (Object.prototype.hasOwnProperty.call(block.input, 'activeForm')) {
              task.activeForm = block.input.activeForm || null;
            }
          }
        }
      } else {
        // All other tools — track for statusline display.
        toolMap.set(block.id, {
          id: block.id,
          name: block.name,
          target: extractTarget(block.name, block.input),
          status: 'running',
          startTime: timestamp,
          endTime: null
        });
      }
    }

    // tool_result: close out open tools, agents, and hydrate task ids.
    if (block.type === 'tool_result' && block.tool_use_id) {
      const tool = toolMap.get(block.tool_use_id);
      if (tool) {
        tool.status = block.is_error ? 'error' : 'completed';
        tool.endTime = timestamp;
      }

      const agent = agentMap.get(block.tool_use_id);
      if (agent) {
        result.statuslineActivityCount += 1;
        hadActivity = true;
        agent.status = 'completed';
        agent.endTime = timestamp;
      }

      const createdTask = latestTodos.find(
        todo => isNativeTaskTodo(todo) && todo._toolUseId === block.tool_use_id
      );
      if (createdTask) {
        const hydratedId = extractTaskIdFromValue(block.content);
        if (hydratedId) {
          createdTask.id = hydratedId;
        }
      }
    }
  }

  if (hadActivity) {
    result.lastActivityAt = timestampIso;
  }
}

/**
 * Pull a displayable target string from a tool's input for statusline use.
 * @param {string} toolName - Tool name (e.g. 'Read', 'Bash')
 * @param {Object} input - Tool input object
 * @returns {string|null} Short target string, or null if not applicable
 */
function extractTarget(toolName, input) {
  if (!input) return null;

  switch (toolName) {
    case 'Read':
    case 'Write':
    case 'Edit':
      return input.file_path ?? input.path ?? null;

    case 'Glob':
    case 'Grep':
      return input.pattern ?? null;

    case 'Bash':
      const cmd = input.command;
      if (!cmd) return null;
      return cmd.length > 30 ? cmd.slice(0, 30) + '...' : cmd;

    default:
      return null;
  }
}

module.exports = {
  parseTranscript,
  processEntry, // exported for unit tests
  extractTarget
};
