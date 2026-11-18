import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

from services.document_processing.normalizer import DocumentNormalizer
from services.document_processing.pymupdf_processor import PyMuPDFProcessor


if len(sys.argv) != 2:
    raise SystemExit("Usage: python test_normalizer.py path/to/file.pdf")

raw_document = PyMuPDFProcessor().extract(sys.argv[1])
normalized_document = DocumentNormalizer().normalize(raw_document)

print(f"Pages: {normalized_document['page_count']}")
print(f"Estimated body font size: {normalized_document['body_font_size']}")
print(f"Normalized blocks: {len(normalized_document['blocks'])}")
print()

for index, block in enumerate(normalized_document["blocks"], start=1):
    print(
        f"{index}. [{block['type']}] "
        f"page={block['page_number']} "
        f"level={block['heading_level']} "
        f"text={block['text'][:180]}"
    )

with open("test_output/normalized_document.json", "w", encoding="utf-8") as file:
    json.dump(normalized_document, file, indent=2)

print("\nFull normalized result saved to:")
print("test_output/normalized_document.json")