from sqlalchemy.orm import Session

from db.models import Document


def find_duplicate_document(
    db: Session,
    workspace_id: int,
    content_hash: str,
    exclude_document_id: int,
) -> Document | None:
    """Find another document with the same hash in the same workspace."""

    return (
        db.query(Document)
        .filter(
            Document.workspace_id == workspace_id,
            Document.content_hash == content_hash,
            Document.id != exclude_document_id,
        )
        .first()
    )