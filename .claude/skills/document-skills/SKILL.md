---
name: tkm:document-skills
description: "Work with office documents in their native formats — Word (.docx), PDF, PowerPoint (.pptx), Excel (.xlsx). Use for document creation, editing, extraction, conversion, and batch processing."
argument-hint: "[docx|pdf|pptx|xlsx] [task]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: specialized-output
triggers: ["Word doc", "PDF", "PowerPoint", "Excel", "office document"]
---

# Reading and Shaping the Commission

Every document format is a different material — each with its own grain, its own resistance, its own way of holding information. The craftsman who works with documents does not treat them as black boxes. They open the format, read what is inside, shape what needs shaping, and return the piece in the form it was meant to take.

## Sub-Skills

Route to the appropriate sub-skill based on the document format:

| Format | Skill | Use For |
|--------|-------|---------|
| `.docx` | `tkm:docx` | Word documents — create, edit, extract, redline, format |
| `.pdf` | `tkm:pdf` | PDFs — extract text/tables, merge, split, fill forms, generate |
| `.pptx` | `tkm:pptx` | PowerPoint — create slides, edit layouts, extract content, generate decks |
| `.xlsx` | `tkm:xlsx` | Excel/spreadsheets — formulas, data analysis, charts, pivot tables |

## When to Activate

- User shares or references a `.docx`, `.pdf`, `.pptx`, or `.xlsx` file
- User asks to create, edit, read, extract, convert, or process an office document
- User needs to fill a PDF form, redline a Word doc, parse spreadsheet data, or generate slides from data
- User says "Word file", "Excel sheet", "PDF report", "PowerPoint deck"

## Routing Logic

```
Received document task
├── .docx or "Word" → load document-skills/docx/SKILL.md
├── .pdf or "PDF"   → load document-skills/pdf/SKILL.md
├── .pptx or "PowerPoint" / "slides" (data-driven) → load document-skills/pptx/SKILL.md
└── .xlsx / .csv / "spreadsheet" / "Excel" → load document-skills/xlsx/SKILL.md
```

> For presentation slides from content or outlines, prefer `tkm:generate-slide` (HTML/PPTX via pptxgenjs). Use `tkm:pptx` when editing or extracting from an **existing** `.pptx` file.

## Installation

Sub-skills require Python libraries. Install once:

```bash
~/.claude/skills/.venv/bin/python3 -m pip install pypdf python-docx openpyxl python-pptx
```

Or run the skill's `install.sh` if present.
