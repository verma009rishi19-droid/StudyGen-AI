import logging
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.document import Document
from app.models.summary import Summary
from app.models.topic import ImportantTopic
from app.models.question_paper import QuestionPaper
from app.models.question import Question
from app.models.history import GenerationHistory
from app.schemas.summary import SummaryOut
from app.schemas.topic import TopicOut
from app.schemas.question_paper import QuestionPaperConfig, QuestionPaperOut
from app.services.ai.factory import get_ai_provider

logger = logging.getLogger("studygen.services.study")

class StudyService:
    @staticmethod
    def _record_history(
        db: Session,
        project_id: int,
        generation_type: str,
        model_used: str,
        status_str: str,
        error_msg: Optional[str] = None
    ):
        try:
            history = GenerationHistory(
                project_id=project_id,
                generation_type=generation_type,
                model_used=model_used,
                status=status_str,
                error_message=error_msg
            )
            db.add(history)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to record history: {e}")
            db.rollback()

    @staticmethod
    async def generate_summary_for_document(db: Session, document_id: int, user_id: int) -> SummaryOut:
        document = db.query(Document).join(Project).filter(
            Document.id == document_id,
            Project.user_id == user_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study document not found or access denied."
            )

        if not document.content or len(document.content.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document content is too short or empty for summary generation."
            )

        ai_provider = get_ai_provider()
        try:
            result = await ai_provider.generate_summary(document.content)
            
            # Save or replace summary for this document
            existing = db.query(Summary).filter(Summary.document_id == document.id).first()
            if existing:
                existing.summary = result.summary
                existing.key_concepts = result.key_concepts
                existing.important_topics = result.important_topics
                existing.quick_revision = result.quick_revision
                summary_record = existing
            else:
                summary_record = Summary(
                    document_id=document.id,
                    summary=result.summary,
                    key_concepts=result.key_concepts,
                    important_topics=result.important_topics,
                    quick_revision=result.quick_revision
                )
                db.add(summary_record)

            db.commit()
            db.refresh(summary_record)

            StudyService._record_history(
                db, document.project_id, "summary", ai_provider.provider_name, "SUCCESS"
            )
            return SummaryOut.model_validate(summary_record)
        except Exception as exc:
            StudyService._record_history(
                db, document.project_id, "summary", ai_provider.provider_name, "FAILED", str(exc)
            )
            logger.error(f"Summary generation failed: {exc}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI generation failed. Please check your AI provider configuration: {exc}"
            )

    @staticmethod
    async def generate_topics_for_document(db: Session, document_id: int, user_id: int) -> List[TopicOut]:
        document = db.query(Document).join(Project).filter(
            Document.id == document_id,
            Project.user_id == user_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study document not found or access denied."
            )

        ai_provider = get_ai_provider()
        try:
            results = await ai_provider.generate_topics(document.content)
            
            # Delete old topics for this document to keep it fresh
            db.query(ImportantTopic).filter(ImportantTopic.document_id == document.id).delete()
            
            created_records = []
            for t in results:
                topic_rec = ImportantTopic(
                    document_id=document.id,
                    topic=t.topic,
                    explanation=t.explanation,
                    importance=t.importance,
                    related_concepts=t.related_concepts
                )
                db.add(topic_rec)
                created_records.append(topic_rec)

            db.commit()
            for rec in created_records:
                db.refresh(rec)

            StudyService._record_history(
                db, document.project_id, "topics", ai_provider.provider_name, "SUCCESS"
            )
            return [TopicOut.model_validate(r) for r in created_records]
        except Exception as exc:
            StudyService._record_history(
                db, document.project_id, "topics", ai_provider.provider_name, "FAILED", str(exc)
            )
            logger.error(f"Topics generation failed: {exc}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate important topics: {exc}"
            )

    @staticmethod
    async def generate_question_paper(
        db: Session, config: QuestionPaperConfig, user_id: int
    ) -> QuestionPaperOut:
        project = db.query(Project).filter(
            Project.id == config.project_id,
            Project.user_id == user_id
        ).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied."
            )

        # Retrieve material
        if config.document_id:
            document = db.query(Document).filter(
                Document.id == config.document_id,
                Document.project_id == project.id
            ).first()
            if not document:
                raise HTTPException(status_code=404, detail="Selected document not found in project.")
            material = document.content
        else:
            docs = db.query(Document).filter(Document.project_id == project.id).all()
            if not docs:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please upload or add study material to this project first."
                )
            material = "\n\n".join([d.content for d in docs])

        ai_provider = get_ai_provider()
        try:
            questions_data = await ai_provider.generate_question_paper(material, config)
            
            qp = QuestionPaper(
                project_id=project.id,
                document_id=config.document_id,
                title=config.title or f"{project.name} Exam Paper",
                total_marks=config.total_marks,
                duration=config.duration,
                difficulty=config.difficulty,
                question_type=config.question_type
            )
            db.add(qp)
            db.flush()

            for q in questions_data:
                q_rec = Question(
                    question_paper_id=qp.id,
                    question_number=q.question_number,
                    question_text=q.question_text,
                    question_type=q.question_type,
                    marks=q.marks,
                    difficulty=q.difficulty,
                    options=q.options,
                    correct_answer=q.correct_answer,
                    explanation=q.explanation
                )
                db.add(q_rec)

            db.commit()
            db.refresh(qp)

            StudyService._record_history(
                db, project.id, "question_paper", ai_provider.provider_name, "SUCCESS"
            )
            return QuestionPaperOut.model_validate(qp)
        except Exception as exc:
            StudyService._record_history(
                db, project.id, "question_paper", ai_provider.provider_name, "FAILED", str(exc)
            )
            logger.error(f"Question paper generation failed: {exc}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Question paper generation failed: {exc}"
            )
