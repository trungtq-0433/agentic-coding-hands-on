# Output Contract

## Final CSV Header

Write this exact 22-column header in English and do not translate it:

`No,itemId,itemName,nameJP,nameTrans,itemType,itemSubtype,buttonType,dataType,required,format,minLength,maxLength,defaultValue,validationNote,description,userAction,transitionNote,databaseTable,databaseColumn,databaseNote,qa`

## Null And Blank Rules

- Convert `N/A`, `None`, `null`, `NULL`, `NA`, and empty-equivalent placeholders into an empty string.
- Keep genuinely unknown values blank instead of inventing replacements.

## Per-Field Processing

Apply these steps to every non-header field in order:

1. Empty check.
   - If the value is null-like, replace it with an empty string.
2. Delimiter sanitization.
   - Replace all commas inside the content with semicolons.
3. Quote escaping.
   - Replace each `"` with `""`.
4. Mandatory wrapping.
   - Wrap every non-empty value in double quotes.
   - Keep real newline characters inside the wrapped value when the content is multiline.

Examples:

- `Error, try again` -> `"Error; try again"`
- `Type "A"` -> `"Type ""A"""`
- multiline content stays multiline inside the same quoted cell.

## Row Construction

1. Write the header once.
2. For each analyzed item:
   - extract exactly 22 fields in header order,
   - process each field with the rules above,
   - join fields with commas,
   - ensure there are exactly 21 commas per row.

## File Paths

- `momorph`: `.momorph/specs/{screenId}-{screen-name}.csv`
- `image` CSV: `.momorph/specs/{source-token}-{screen-name}.csv`
- `image` bbox JSON: `.momorph/specs/{source-token}-{screen-name}-item-bboxes.json`
- `image` annotated preview: `.momorph/specs/{source-token}-{screen-name}-item-bboxes-annotated.png`

Use raw CSV content only. Do not wrap the file content in markdown code fences.

## Image-Only BBox JSON

For `image` mode, write the bbox sidecar as a JSON array in visual order. Each entry must use this exact shape:

```json
{
   "itemNo": "1",
   "position": {
      "startX": 0,
      "startY": 0,
      "endX": 1200,
      "endY": 56
   }
}
```

- `itemNo` must exactly match the CSV `No` value for the same item.
- `position` uses original-image pixel space with `startX <= endX` and `startY <= endY`.
- Maximum `itemNo` depth is 3.

## Image-Only Annotated Preview

For `image` mode, draw one rectangle and one visible `itemNo` label per bbox entry.

- Use the original source image dimensions with no rescaling or cropping.
- Save the annotated preview as `.momorph/specs/{source-token}-{screen-name}-item-bboxes-annotated.png`.
- Keep the bbox JSON and annotated preview additive; they must not change the 22-column CSV contract.

## Output Discipline

- Keep header names in English exactly as shown.
- Keep cell content in the chosen `targetLanguage`, except `nameJP` which stays Japanese and `nameTrans` which stays English.
- Preserve real newlines inside multiline cells.
- Leave blank cells blank.