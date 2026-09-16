import re
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.question_paper import QuestionPaper
from app.models.question import Question
from app.models.quiz import QuizAttempt
from app.models.project import Project
from app.schemas.quiz import QuizSubmitRequest, QuizAttemptOut

class QuizService:
    @staticmethod
    def _is_answer_correct(user_ans: str, correct_ans: str, q_type: str) -> bool:
        u_clean = user_ans.strip().lower()
        c_clean = correct_ans.strip().lower()

        if not u_clean:
            return False

        if q_type == "MCQ":
            # Exact match or starts with same option letter (e.g. "A" or "A. ...")
            if u_clean == c_clean:
                return True
            # Strip option prefixes like "A) ", "A. ", "1. "
            u_core = re.sub(r"^[a-d0-9][\.\)\s]+", "", u_clean).strip()
            c_core = re.sub(r"^[a-d0-9][\.\)\s]+", "", c_clean).strip()
            if u_core and c_core and (u_core == c_core or u_core in c_clean or c_core in u_clean):
                return True
            return False
        else:
            # For short answers: check key phrase/term overlap
            if u_clean == c_clean:
                return True
            # Significant word overlap
            u_words = set(re.findall(r"\b\w{4,}\b", u_clean))
            c_words = set(re.findall(r"\b\w{4,}\b", c_clean))
            if not c_words:
                return u_clean in c_clean or c_clean in u_clean
            overlap = len(u_words.intersection(c_words))
            return (overlap / len(c_words)) >= 0.4

    @staticmethod
    def evaluate_quiz(db: Session, request: QuizSubmitRequest, user_id: int) -> QuizAttemptOut:
        qp = db.query(QuestionPaper).join(Project).filter(
            QuestionPaper.id == request.question_paper_id
        ).first()

        if not qp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question paper not found."
            )

        # Build answers map
        user_answers: Dict[int, str] = {a.question_id: a.user_answer for a in request.answers}

        questions = qp.questions
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question paper contains no questions."
            )

        total_questions = len(questions)
        correct_count = 0
        details: List[Dict[str, Any]] = []
        earned_marks = 0.0

        for q in questions:
            u_ans = user_answers.get(q.id, "")
            is_correct = QuizService._is_answer_correct(u_ans, q.correct_answer, q.question_type)
            if is_correct:
                correct_count += 1
                earned_marks += q.marks

            details.append({
                "question_id": q.id,
                "question_number": q.question_number,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "marks": q.marks,
                "options": q.options,
                "user_answer": u_ans,
                "correct_answer": q.correct_answer,
                "is_correct": is_correct,
                "explanation": q.explanation or "Directly verified against study text."
            })

        incorrect_count = total_questions - correct_count
        percentage = round((correct_count / total_questions) * 100.0, 1) if total_questions > 0 else 0.0

        attempt = QuizAttempt(
            user_id=user_id,
            question_paper_id=qp.id,
            score=earned_marks,
            total_questions=total_questions,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            percentage=percentage,
            details=details
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return QuizAttemptOut.model_validate(attempt)
