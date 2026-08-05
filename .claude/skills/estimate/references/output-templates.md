# Output Templates Index

Templates for generating estimation reports. Two tiers based on input quality.

## Template Selection

Use **Bidding-grade** when input has ≥3 of {user stories, screen list, tech stack, NFR, actor list}. Otherwise **Quick**.

| Input Quality | Template | File |
|---------------|----------|------|
| Brief spec / feature list | Quick | [output-template-quick.md](output-template-quick.md) |
| Detailed spec with user stories, screens, tech stack | Bidding-grade | [output-template-bidding.md](output-template-bidding.md) |

## Usage

1. Determine template tier using selection rule above
2. Load ONLY the relevant template file (not both)
3. For Excel/PDF output, see JSON schema in quick template file
