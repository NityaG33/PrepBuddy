import unittest

from services.document_processing.normalizer import DocumentNormalizer


class TestDocumentNormalizer(unittest.TestCase):
    def setUp(self):
        self.normalizer = DocumentNormalizer()

    def test_detects_heading_paragraph_and_list_item(self):
        raw_document = {
            "metadata": {"title": "Sample Document"},
            "page_count": 1,
            "pages": [
                {
                    "page_number": 1,
                    "blocks": [
                        {
                            "bbox": (50, 50, 300, 70),
                            "lines": [
                                {
                                    "bbox": (50, 50, 300, 70),
                                    "spans": [
                                        {
                                            "text": "1. Introduction",
                                            "bbox": (50, 50, 300, 70),
                                            "font": "Arial-Bold",
                                            "font_size": 18.0,
                                            "flags": 16,
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "bbox": (50, 100, 500, 115),
                            "lines": [
                                {
                                    "bbox": (50, 100, 500, 115),
                                    "spans": [
                                        {
                                            "text": "Machine learning is a field",
                                            "bbox": (50, 100, 500, 115),
                                            "font": "Arial",
                                            "font_size": 12.0,
                                            "flags": 0,
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "bbox": (50, 118, 500, 133),
                            "lines": [
                                {
                                    "bbox": (50, 118, 500, 133),
                                    "spans": [
                                        {
                                            "text": "that uses data to learn patterns.",
                                            "bbox": (50, 118, 500, 133),
                                            "font": "Arial",
                                            "font_size": 12.0,
                                            "flags": 0,
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "bbox": (70, 150, 400, 165),
                            "lines": [
                                {
                                    "bbox": (70, 150, 400, 165),
                                    "spans": [
                                        {
                                            "text": "• Supervised learning",
                                            "bbox": (70, 150, 400, 165),
                                            "font": "Arial",
                                            "font_size": 12.0,
                                            "flags": 0,
                                        }
                                    ],
                                }
                            ],
                        },
                    ],
                }
            ],
        }

        document = self.normalizer.normalize(raw_document)
        blocks = document["blocks"]

        self.assertEqual(document["page_count"], 1)
        self.assertEqual(len(blocks), 3)

        self.assertEqual(blocks[0]["type"], "heading")
        self.assertEqual(blocks[0]["heading_level"], 1)
        self.assertEqual(blocks[0]["text"], "1. Introduction")

        self.assertEqual(blocks[1]["type"], "paragraph")
        self.assertEqual(
            blocks[1]["text"],
            "Machine learning is a field that uses data to learn patterns.",
        )
        self.assertEqual(blocks[1]["source_block_count"], 2)

        self.assertEqual(blocks[2]["type"], "list_item")
        self.assertEqual(blocks[2]["text"], "• Supervised learning")
        self.assertEqual(len(document["pages"]), 1)
        self.assertEqual(document["pages"][0]["page"], 1)

        self.assertEqual(
            document["pages"][0]["text"],
            (
                "1. Introduction\n\n"
                "Machine learning is a field "
                "that uses data to learn patterns.\n\n"
                "• Supervised learning"
            ),
        )

    def test_empty_document_returns_no_blocks(self):
        raw_document = {
            "metadata": {},
            "page_count": 0,
            "pages": [],
        }

        document = self.normalizer.normalize(raw_document)

        self.assertEqual(document["blocks"], [])
        self.assertEqual(document["page_count"], 0)
        self.assertEqual(document["body_font_size"], 12.0)

    def test_textless_page_is_preserved_with_empty_text(self):
        raw_document = {
            "metadata": {},
            "page_count": 1,
            "pages": [
                {
                    "page_number": 1,
                    "blocks": [],
                }
            ],
        }

        document = self.normalizer.normalize(raw_document)

        self.assertEqual(len(document["pages"]), 1)
        self.assertEqual(document["pages"][0]["page"], 1)
        self.assertEqual(document["pages"][0]["text"], "")
        self.assertEqual(document["pages"][0]["blocks"], [])


if __name__ == "__main__":
    unittest.main()