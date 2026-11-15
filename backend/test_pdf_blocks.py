
from services.pdf_service import extract_text_from_pdf

PDF_PATH = "uploads/Gradient Descent Method.pdf"

# 1. Extract PDF
result = extract_text_from_pdf(PDF_PATH)

# 2. Check document metadata
print("\n========== METADATA ==========")
print(result["metadata"])

# 3. Check total pages
pages = result["pages"]

print("\n========== PAGE COUNT ==========")
print("Total pages:", len(pages))

assert len(pages) > 0, "No pages extracted!"

# 4. Check every page
for page in pages:

    print(f"\n========== PAGE {page['page']} ==========")

    assert "text" in page
    assert "blocks" in page

    print("Text length:", len(page["text"]))
    print("Total blocks:", len(page["blocks"]))

    # 5. Check every block
    for block in page["blocks"]:

        assert block["text"].strip(), "Empty text block!"
        assert "bbox" in block
        assert "font_sizes" in block
        assert "fonts" in block
        assert "is_bold" in block
        assert "type" in block
        assert "level" in block
        assert "heading_confidence" in block

# 6. Check first page text
print("\n========== FIRST PAGE TEXT ==========")
print(pages[0]["text"])

# 7. Check first page blocks
print("\n========== FIRST PAGE BLOCKS ==========")

for block in pages[0]["blocks"]:

    print("\nText:", block["text"])
    print("Position:", block["bbox"])
    print("Fonts:", block["fonts"])
    print("Font sizes:", block["font_sizes"])
    print("Bold:", block["is_bold"])
    print("Type:", block["type"])
    print("Level:", block["level"])
    print("Confidence:", block["heading_confidence"])

print("\nALL EXTRACTION TESTS PASSED!")



# # Additional validation: coordinates and font information

# print("\n========== LAYOUT VALIDATION ==========")

# total_blocks = 0

# for page in result["pages"]:

#     for block in page["blocks"]:

#         total_blocks += 1

#         bbox = block["bbox"]

#         # Check bounding box
#         assert len(bbox) == 4, "Invalid bounding box"

#         x0, y0, x1, y1 = bbox

#         assert x1 >= x0, "Invalid horizontal coordinates"
#         assert y1 >= y0, "Invalid vertical coordinates"

#         # Check font information
#         assert len(block["font_sizes"]) > 0
#         assert len(block["fonts"]) > 0

#         assert all(size > 0 for size in block["font_sizes"])

#         # Check classification
#         assert block["type"] in ["heading", "paragraph"]

# print("Total blocks checked:", total_blocks)
# print("Coordinates: Valid")
# print("Font information: Available")
# print("Block classification: Valid")
# print("\nLAYOUT VALIDATION PASSED!")



# for page in result["pages"][1:5]:

#     print(f"\n{'=' * 70}")
#     print(f"PAGE {page['page']}")
#     print(f"{'=' * 70}")

#     for block in page["blocks"]:
#         print(
#             f"\nType: {block['type']}"
#             f"\nLevel: {block['level']}"
#             f"\nConfidence: {block['heading_confidence']}"
#             f"\nFont sizes: {block['font_sizes']}"
#             f"\nBold: {block['is_bold']}"
#             f"\nText: {block['text'][:200]}"
#         )


page = result["pages"][4]

for i, block in enumerate(page["blocks"]):
    print(f"\nBLOCK {i}")

    print("Text:", repr(block["text"]))
    print("Bounding box:", block["bbox"])
    print("Font sizes:", block["font_sizes"])
    print("Fonts:", block["fonts"])