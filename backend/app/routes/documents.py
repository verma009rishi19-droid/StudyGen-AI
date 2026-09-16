from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentOut
from app.schemas.common import MessageResponse
from app.utils.security import get_optional_user
from app.routes.projects import resolve_user
from app.utils.text_processing import clean_text

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_text_document(
    request: DocumentCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    project = db.query(Project).filter(
        Project.id == request.project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied.")

    cleaned_content = clean_text(request.content)
    if len(cleaned_content) < 10:
        raise HTTPException(status_code=400, detail="Study material content must be at least 10 characters.")

    doc = Document(
        project_id=project.id,
        filename=request.filename or "Pasted Study Material.txt",
        file_type="text",
        content=cleaned_content,
        char_count=len(cleaned_content)
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)

@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document_file(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied.")

    # Validate file extension
    filename = file.filename or "uploaded_study_material.txt"
    lower_fn = filename.lower()
    is_pdf = lower_fn.endswith(".pdf")
    is_text = lower_fn.endswith(".txt") or lower_fn.endswith(".md")

    if not (is_pdf or is_text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a .pdf, .txt, or .md document."
        )

    content_bytes = await file.read()

    if is_pdf:
        from app.utils.text_processing import extract_text_from_pdf
        try:
            content_str = extract_text_from_pdf(content_bytes)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not parse PDF: {str(exc)}"
            )

        if len(content_str) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded PDF contains no selectable text (it may be a scanned image or protected). Please use a text-based PDF or paste your study notes."
            )
        doc_type = "file/pdf"
        cleaned = content_str
    else:
        try:
            content_str = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_str = content_bytes.decode("latin-1")
            except Exception:
                raise HTTPException(status_code=400, detail="Could not decode text file. Ensure it is UTF-8 encoded.")

        cleaned = clean_text(content_str)
        if len(cleaned) < 10:
            raise HTTPException(status_code=400, detail="Uploaded file contains insufficient text (minimum 10 characters).")
        doc_type = "file/txt"

    doc = Document(
        project_id=project.id,
        filename=filename,
        file_type=doc_type,
        content=cleaned,
        char_count=len(cleaned)
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)

@router.get("/project/{project_id}", response_model=List[DocumentOut])
def list_project_documents(
    project_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied.")

    docs = db.query(Document).filter(Document.project_id == project.id).order_by(Document.created_at.desc()).all()
    return [DocumentOut.model_validate(d) for d in docs]

@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    doc = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")

    return DocumentOut.model_validate(doc)

@router.delete("/{document_id}", response_model=MessageResponse)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    current_user = resolve_user(db, user)
    doc = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")

    db.delete(doc)
    db.commit()
    return MessageResponse(message="Document deleted successfully.")
