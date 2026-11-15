
from pathlib import Path
from time import perf_counter
import json

from docling.document_converter import DocumentConverter

# Select one PDF for our initial experiment
PDF_PATH = Path("test_pdfs/9_Linear Regression- Gradient Descent Method.pdf")

OUTPUT_DIR = Path("docling_output")
OUTPUT_DIR.mkdir(exist_ok=True)

print("Initializing Docling...")
converter = DocumentConverter()

print(f"\nConverting: {PDF_PATH.name}")

start_time = perf_counter()
result = converter.convert(PDF_PATH)
processing_time = perf_counter() - start_time

# Export the structured document to Markdown
markdown_text = result.document.export_to_markdown()

# Export the structured document to JSON
json_data = result.document.export_to_dict()

markdown_path = OUTPUT_DIR / f"{PDF_PATH.stem}.md"
json_path = OUTPUT_DIR / f"{PDF_PATH.stem}.json"

markdown_path.write_text(markdown_text, encoding="utf-8")

with json_path.open("w", encoding="utf-8") as file:
    json.dump(json_data, file, indent=2, ensure_ascii=False)

# Basic statistics
print("\n========== RESULTS ==========")
print("PDF:", PDF_PATH.name)
print("Processing time:", round(processing_time, 2), "seconds")
print("Markdown characters:", len(markdown_text))
print("JSON top-level keys:", list(json_data.keys()))

print("\n========== MARKDOWN PREVIEW ==========")
print(markdown_text[:5000])

print("\nSaved files:")
print(markdown_path)
print(json_path)
