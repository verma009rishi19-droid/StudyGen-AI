import re
from typing import List
from app.services.ai.base import BaseAIProvider
from app.schemas.summary import SummaryResult
from app.schemas.topic import ImportantTopicResult
from app.schemas.question_paper import QuestionPaperConfig, QuestionResult
from app.utils.text_processing import clean_text, extract_sentences, extract_keywords_and_headings

class FallbackAIProvider(BaseAIProvider):
    """
    Deterministic rule-based study extraction provider.
    Provides immediate zero-dependency study generation strictly extracted from study material,
    enabling unit tests and reliable fallback when local/cloud LLMs are not running.
    """
    @property
    def provider_name(self) -> str:
        return "internal:heuristic-fallback"

    async def generate_summary(self, material: str) -> SummaryResult:
        cleaned = clean_text(material)
        sentences = extract_sentences(cleaned)
        
        # Build concise executive summary
        summary_body = " ".join(sentences[:5]) if sentences else cleaned[:300]
        
        # Extract potential key concepts
        words = re.findall(r"\b[A-Za-z]{4,}\b", cleaned)
        freq = {}
        for w in words:
            w_lower = w.lower()
            if w_lower not in {"this", "that", "with", "from", "have", "were", "which", "about", "their", "there", "these", "other"}:
                freq[w.capitalize()] = freq.get(w.capitalize(), 0) + 1
        sorted_concepts = sorted(freq.keys(), key=lambda k: freq[k], reverse=True)[:6]
        if not sorted_concepts:
            sorted_concepts = ["Key Theme", "Core Structure", "Primary Mechanism"]

        # Extract topics
        headings = extract_keywords_and_headings(cleaned)
        topics = headings[:5] if headings else [f"Analysis of {c}" for c in sorted_concepts[:4]]

        # Quick revision bullet points
        quick_rev = [s for s in sentences if 20 <= len(s) <= 180][:6]
        if not quick_rev:
            quick_rev = [f"Primary focus centers on {sorted_concepts[0]}.", "Crucial to understand fundamental relationships."]

        return SummaryResult(
            summary=summary_body,
            key_concepts=sorted_concepts,
            important_topics=topics,
            quick_revision=quick_rev
        )

    async def generate_topics(self, material: str) -> List[ImportantTopicResult]:
        cleaned = clean_text(material)
        sentences = extract_sentences(cleaned)
        headings = extract_keywords_and_headings(cleaned)

        results: List[ImportantTopicResult] = []
        if headings:
            for i, h in enumerate(headings[:6]):
                # Find sentence containing heading or related concept
                expl = next((s for s in sentences if h.lower() in s.lower()), None)
                if not expl and i < len(sentences):
                    expl = sentences[i]
                elif not expl:
                    expl = f"Crucial study topic examining {h} and its fundamental operational attributes."
                
                importance = "Critical" if i < 2 else ("High" if i < 4 else "Medium")
                results.append(ImportantTopicResult(
                    topic=h,
                    explanation=expl,
                    importance=importance,
                    related_concepts=[f"{h} Architecture", "Theoretical Foundation"]
                ))
        else:
            # Fallback topics from sentences
            for i in range(min(4, len(sentences))):
                topic_name = f"Core Topic {i+1}"
                results.append(ImportantTopicResult(
                    topic=topic_name,
                    explanation=sentences[i],
                    importance="High",
                    related_concepts=["Study Fundamentals", "Practical Applications"]
                ))

        if not results:
            results.append(ImportantTopicResult(
                topic="General Overview",
                explanation=cleaned[:250],
                importance="High",
                related_concepts=["Core Knowledge"]
            ))

        return results

    async def generate_question_paper(
        self, material: str, config: QuestionPaperConfig
    ) -> List[QuestionResult]:
        cleaned = clean_text(material)
        sentences = extract_sentences(cleaned)
        num_q = config.num_questions
        marks_per_q = max(1, config.total_marks // num_q)
        results: List[QuestionResult] = []

        for i in range(num_q):
            idx = i % max(1, len(sentences))
            sentence = sentences[idx] if sentences else f"Core principle regarding question {i+1}."
            
            # Determine question type
            if config.question_type == "MCQ" or (config.question_type == "Mixed" and i % 2 == 0):
                q_type = "MCQ"
                options = [
                    f"{sentence[:60]}",
                    "Contradictory hypothesis not supported by text",
                    "Unrelated peripheral assumption",
                    "Alternative theoretical formulation"
                ]
                results.append(QuestionResult(
                    question_number=i + 1,
                    question_text=f"Which of the following statements accurately reflects the study material on this topic?",
                    question_type=q_type,
                    marks=marks_per_q,
                    difficulty=config.difficulty,
                    options=options,
                    correct_answer=options[0],
                    explanation=f"Based directly on the study text: '{sentence}'"
                ))
            elif config.question_type == "Short Answer" or (config.question_type == "Mixed" and i % 2 != 0):
                results.append(QuestionResult(
                    question_number=i + 1,
                    question_text=f"Explain the significance of the following statement: '{sentence[:90]}...'",
                    question_type="Short Answer",
                    marks=marks_per_q,
                    difficulty=config.difficulty,
                    options=[],
                    correct_answer=sentence,
                    explanation=f"Key concept explanation: {sentence}"
                ))
            else:
                results.append(QuestionResult(
                    question_number=i + 1,
                    question_text=f"Critically analyze the core mechanisms and implications discussed regarding: '{sentence[:80]}'",
                    question_type="Long Answer",
                    marks=marks_per_q,
                    difficulty=config.difficulty,
                    options=[],
                    correct_answer=f"Comprehensive breakdown should cover: 1) Definition; 2) Key properties: {sentence}; 3) Applications.",
                    explanation=f"Expected answer should synthesize the provided material regarding {sentence}."
                ))

        return results
