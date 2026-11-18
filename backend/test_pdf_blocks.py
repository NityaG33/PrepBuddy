from services.document_processing.pipeline import (
    create_default_document_processing_pipeline,
)


PDF_PATH = "uploads/Gradient Descent Method.pdf"

document_processing_pipeline = (
    create_default_document_processing_pipeline()
)

result = document_processing_pipeline.process(PDF_PATH)

print("\n========== METADATA ==========")
print(result["metadata"])

pages = result["pages"]

print("\n========== PAGE COUNT ==========")
print("Total pages:", len(pages))

assert len(pages) > 0, "No pages extracted!"

for page in pages:
    print(f"\n========== PAGE {page['page']} ==========")

    assert "text" in page
    assert "blocks" in page

    print("Text length:", len(page["text"]))
    print("Total blocks:", len(page["blocks"]))

    for block in page["blocks"]:
        assert block["text"].strip(), "Empty text block!"
        assert "bbox" in block
        assert "font_size" in block
        assert "is_bold" in block
        assert "type" in block
        assert "heading_level" in block
        assert "source_block_count" in block

print("\n========== FIRST PAGE TEXT ==========")
print(pages[0]["text"])

print("\n========== FIRST PAGE BLOCKS ==========")

for block in pages[0]["blocks"]:
    print("\nText:", block["text"])
    print("Position:", block["bbox"])
    print("Average font size:", block["font_size"])
    print("Bold:", block["is_bold"])
    print("Type:", block["type"])
    print("Heading level:", block["heading_level"])
    print("Merged source blocks:", block["source_block_count"])

print("\nALL NORMALIZATION CHECKS PASSED!")