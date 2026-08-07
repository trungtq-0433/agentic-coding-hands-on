/**
 * Helper THUẦN (không React, không DOM) áp định dạng markdown-nhẹ lên vùng
 * chọn của textarea lời cảm ơn.
 *
 * `ComposeKudoDraft.body` lưu dạng text thuần — không có cột/schema rich-text
 * nào khác (xem `compose-kudo-types.ts`). Ký hiệu markdown (`**bold**`,
 * `_italic_`, `~~stroke~~`, `1. ` số, `> ` quote, `[chữ](url)` link,
 * `@Tên ` mention) là cách MVP biểu đạt định dạng ngay trong chuỗi đó, không
 * cần đổi contract `draft`. Tách khỏi component để test được không cần DOM.
 */

export interface SelectionRange {
  start: number;
  end: number;
}

export interface FormatResult {
  value: string;
  range: SelectionRange;
}

/** Bọc/gỡ một token đối xứng (`**`, `_`, `~~`) quanh đúng vùng đang chọn — hành vi "toggle". */
function wrapToken(value: string, range: SelectionRange, token: string): FormatResult {
  const { start, end } = range;
  const selected = value.slice(start, end);
  const alreadyWrapped =
    selected.length >= token.length * 2 && selected.startsWith(token) && selected.endsWith(token);

  if (alreadyWrapped) {
    const inner = selected.slice(token.length, selected.length - token.length);
    return {
      value: value.slice(0, start) + inner + value.slice(end),
      range: { start, end: start + inner.length },
    };
  }

  return {
    value: value.slice(0, start) + token + selected + token + value.slice(end),
    range: { start: start + token.length, end: start + token.length + selected.length },
  };
}

export function toggleBold(value: string, range: SelectionRange): FormatResult {
  return wrapToken(value, range, "**");
}

export function toggleItalic(value: string, range: SelectionRange): FormatResult {
  return wrapToken(value, range, "_");
}

export function toggleStroke(value: string, range: SelectionRange): FormatResult {
  return wrapToken(value, range, "~~");
}

/**
 * Thêm/gỡ tiền tố ở ĐẦU MỖI DÒNG trong khối chứa vùng chọn (dùng cho danh
 * sách đánh số + trích dẫn). Toggle: nếu MỌI dòng không rỗng đã có tiền tố
 * thì gỡ hết, ngược lại thêm cho những dòng còn thiếu.
 */
function toggleLinePrefix(
  value: string,
  range: SelectionRange,
  prefixFor: (lineIndex: number) => string,
  stripPattern: RegExp,
): FormatResult {
  const blockStart = value.lastIndexOf("\n", range.start - 1) + 1;
  const nextBreak = value.indexOf("\n", range.end);
  const blockEnd = nextBreak === -1 ? value.length : nextBreak;

  const block = value.slice(blockStart, blockEnd);
  const lines = block.split("\n");
  const nonEmptyLines = lines.filter((line) => line.trim() !== "");
  const allPrefixed = nonEmptyLines.length > 0 && nonEmptyLines.every((line) => stripPattern.test(line));

  const nextLines = lines.map((line, index) => {
    if (line.trim() === "") return line;
    if (allPrefixed) return line.replace(stripPattern, "");
    return `${prefixFor(index)}${line}`;
  });
  const nextBlock = nextLines.join("\n");

  return {
    value: value.slice(0, blockStart) + nextBlock + value.slice(blockEnd),
    range: { start: blockStart, end: blockStart + nextBlock.length },
  };
}

export function toggleNumberedList(value: string, range: SelectionRange): FormatResult {
  return toggleLinePrefix(value, range, (index) => `${index + 1}. `, /^\d+\.\s/);
}

export function toggleQuote(value: string, range: SelectionRange): FormatResult {
  return toggleLinePrefix(value, range, () => "> ", /^>\s?/);
}

/** Thay thế đúng vùng `range` bằng `insertText`, con trỏ đặt ở CUỐI đoạn vừa chèn. */
export function replaceRange(value: string, range: SelectionRange, insertText: string): FormatResult {
  const nextValue = value.slice(0, range.start) + insertText + value.slice(range.end);
  const cursor = range.start + insertText.length;
  return { value: nextValue, range: { start: cursor, end: cursor } };
}

/**
 * Tìm "@tên đang gõ dở" ngay trước vị trí con trỏ — kích hoạt gợi ý mention.
 * Chỉ khớp khi "@" đứng sau khoảng trắng hoặc đầu chuỗi, và chưa gõ khoảng
 * trắng nào sau "@" (còn đang gõ dở tên).
 */
export function findMentionQuery(value: string, cursor: number): { start: number; query: string } | null {
  const upToCursor = value.slice(0, cursor);
  const match = /(?:^|\s)@([^\s@]*)$/.exec(upToCursor);
  if (!match) return null;
  const query = match[1] ?? "";
  return { start: cursor - query.length - 1, query };
}

/** Thay `@queryĐangGõ` bằng `@TênĐầyĐủ ` (có khoảng trắng cuối để tách khỏi chữ tiếp theo). */
export function insertMention(value: string, mentionStart: number, queryLength: number, name: string): FormatResult {
  return replaceRange(value, { start: mentionStart, end: mentionStart + 1 + queryLength }, `@${name} `);
}
