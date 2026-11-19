# Document Processing Limitations

PrepBuddy currently uses PyMuPDF to extract selectable text and a heuristic
normalizer to identify headings, paragraphs, and list items. The following
limitations are known and intentional for Phase 2.

## Heading classification

Headings are inferred from font size, boldness, numbering, and short-text
patterns. A visually styled title can be classified as a paragraph when its
font information is inconsistent or when it is grouped with nearby content.
Conversely, a short bold paragraph can be classified as a heading.

## Paragraph reconstruction

Nearby blocks may be merged when they appear to continue an unfinished
paragraph. PDFs that use columns, cards, callouts, or unusual spacing can
split or merge content in a way that does not match the original authoring
intent.

## Tables and equations

Table cells and mathematical equations are often stored as independently
positioned fragments. Their reading order and semantic relationships are not
reconstructed reliably in this phase. PrepBuddy preserves extracted text and
coordinates where available, but does not yet provide table reconstruction or
mathematical-layout understanding.

## Multi-column and slide layouts

The current reading order uses PyMuPDF's sorted text blocks. Multi-column
pages, presentation slides, and card-based layouts can expose several visual
items as one block or return an order that differs from the visual order.
List counts can therefore reflect list groups rather than individual bullets.

## Scanned PDFs and OCR

Scanned or image-only PDFs are detected as having no extractable text and are
reported clearly to the user. OCR is deliberately out of scope for Phase 2
and has not been introduced.
