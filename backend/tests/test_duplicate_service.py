from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database import Base
from db.models import Workspace, Document
from services.duplicate_service import find_duplicate_document


def setup_database():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    return engine, Session()


def create_document(
    db,
    workspace_id,
    content_hash,
    filename="test.pdf",
):
    document = Document(
        workspace_id=workspace_id,
        filename=filename,
        file_path=f"uploads/{filename}",
        content_hash=content_hash,
        status="indexed",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def test_finds_duplicate_in_same_workspace():
    engine, db = setup_database()

    try:
        workspace = Workspace(name="Workspace 1")
        db.add(workspace)
        db.commit()

        original = create_document(
            db,
            workspace.id,
            "abc123",
            "original.pdf",
        )

        duplicate = find_duplicate_document(
            db=db,
            workspace_id=workspace.id,
            content_hash="abc123",
            exclude_document_id=-1,
        )

        assert duplicate is not None
        assert duplicate.id == original.id

    finally:
        db.close()
        engine.dispose()


def test_does_not_find_duplicate_in_different_workspace():
    engine, db = setup_database()

    try:
        workspace_one = Workspace(name="Workspace 1")
        workspace_two = Workspace(name="Workspace 2")

        db.add_all([workspace_one, workspace_two])
        db.commit()

        create_document(
            db,
            workspace_one.id,
            "abc123",
            "original.pdf",
        )

        duplicate = find_duplicate_document(
            db=db,
            workspace_id=workspace_two.id,
            content_hash="abc123",
            exclude_document_id=-1,
        )

        assert duplicate is None

    finally:
        db.close()
        engine.dispose()


def test_excludes_current_document():
    engine, db = setup_database()

    try:
        workspace = Workspace(name="Workspace 1")
        db.add(workspace)
        db.commit()

        original = create_document(
            db,
            workspace.id,
            "abc123",
            "original.pdf",
        )

        duplicate = find_duplicate_document(
            db=db,
            workspace_id=workspace.id,
            content_hash="abc123",
            exclude_document_id=original.id,
        )

        assert duplicate is None

    finally:
        db.close()
        engine.dispose()