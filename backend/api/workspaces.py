import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Document, Workspace
from vectorstore.store import get_vector_store, save_vector_store

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"],
)


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WorkspaceUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@router.post("")
def create_workspace(
    request: WorkspaceCreate,
    db: Session = Depends(get_db),
):
    name = request.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Workspace name cannot be empty",
        )

    workspace = Workspace(name=name)

    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    return {
        "id": workspace.id,
        "name": workspace.name,
        "created_at": workspace.created_at,
    }


@router.get("")
def list_workspaces(
    db: Session = Depends(get_db),
):
    workspaces = (
        db.query(Workspace)
        .order_by(Workspace.created_at.asc())
        .all()
    )

    return {
        "workspaces": [
            {
                "id": workspace.id,
                "name": workspace.name,
                "created_at": workspace.created_at,
            }
            for workspace in workspaces
        ]
    }


@router.get("/{workspace_id}")
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
):
    workspace = db.get(Workspace, workspace_id)

    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )

    return {
        "id": workspace.id,
        "name": workspace.name,
        "created_at": workspace.created_at,
    }


@router.patch("/{workspace_id}")
def rename_workspace(
    workspace_id: int,
    request: WorkspaceUpdate,
    db: Session = Depends(get_db),
):
    workspace = db.get(Workspace, workspace_id)

    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )

    name = request.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Workspace name cannot be empty",
        )

    workspace.name = name
    db.commit()
    db.refresh(workspace)

    return {
        "message": "Workspace renamed successfully",
        "id": workspace.id,
        "name": workspace.name,
    }


@router.delete("/{workspace_id}")
def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
):
    workspace = db.get(Workspace, workspace_id)

    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )

    document_count = (
        db.query(Document)
        .filter(Document.workspace_id == workspace_id)
        .count()
    )

    if document_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Delete or move all documents before deleting this workspace",
        )

    db.delete(workspace)
    db.commit()

    return {
        "message": "Workspace deleted successfully",
        "workspace_id": workspace_id,
    }


@router.delete("/{workspace_id}/documents")
def delete_workspace_documents(
    workspace_id: int,
    db: Session = Depends(get_db),
):
    # 1. Find the workspace
    workspace = db.get(Workspace, workspace_id)

    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )

    # 2. Get all documents in this workspace
    documents = (
        db.query(Document)
        .filter(Document.workspace_id == workspace_id)
        .all()
    )

    if not documents:
        return {
            "message": "Workspace contains no documents",
            "workspace_id": workspace_id,
            "deleted_documents": 0,
            "removed_chunks": 0,
        }

    # 3. Collect document IDs and file paths
    document_ids = {document.id for document in documents}

    file_paths = [
        document.file_path
        for document in documents
        if document.file_path
    ]

    # 4. Remove all matching chunks from FAISS
    vector_store = get_vector_store()
    removed_chunks = 0

    if vector_store is not None:
        removed_chunks = vector_store.remove_documents(
            document_ids
        )
        save_vector_store()

    # 5. Delete database records
    deleted_count = len(documents)

    try:
        for document in documents:
            db.delete(document)

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not delete workspace documents",
        )

    # 6. Delete uploaded PDF files
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            # Log the error for later cleanup
            pass

    return {
        "message": "All workspace documents deleted successfully",
        "workspace_id": workspace_id,
        "deleted_documents": deleted_count,
        "removed_chunks": removed_chunks,
    }