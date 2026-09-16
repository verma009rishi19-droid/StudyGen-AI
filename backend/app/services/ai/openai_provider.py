import json
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI

from app.services.ai.base import BaseAIProvider
from app.services.ai.fallback_provider import FallbackAIProvider
from app.schemas.summary import SummaryResult
from app.schemas.topic import ImportantTopicResult
from app.schemas.question_paper import QuestionPaperConfig, QuestionResult
from app.utils.text_processing import truncate_text

logger = logging.getLogger("studygen.ai.openai")

class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.fallback = FallbackAIProvider()

    @property
    def provider_name(self) -> str:
        return f"openai:{self.model}"

    async def _call_openai_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        if not self.client:
            raise ValueError("OpenAI API key is not configured.")

        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt + "\nOutput valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        content = response.choices[0].message.content
        return json.loads(content or "{}")

    async def generate_summary(self, material: str) -> SummaryResult:
        if not self.client:
            return await self.fallback.generate_summary(material)

        system_prompt = (
            "You are an academic study assistant. Extract a structured summary strictly from the provided material. "
            "Return JSON with keys: "
            "'summary' (detailed overview string), "
            "'key_concepts' (array of strings), "
            "'important_topics' (array of strings), "
            "'quick_revision' (array of bullet point strings)."
        )
        prompt = f"Study Material:\n{truncate_text(material, 15000)}"

        try:
            raw = await self._call_openai_json(prompt, system_prompt)
            return SummaryResult(
                summary=raw.get("summary", ""),
                key_concepts=raw.get("key_concepts", []),
                important_topics=raw.get("important_topics", []),
                quick_revision=raw.get("quick_revision", [])
            )
        except Exception as exc:
            logger.warning(f"OpenAI call failed ({exc}). Using internal heuristic fallback.")
            return await self.fallback.generate_summary(material)

    async def generate_topics(self, material: str) -> List[ImportantTopicResult]:
        if not self.client:
            return await self.fallback.generate_topics(material)

        system_prompt = (
            "Extract key exam preparation topics from the study material. "
            "Return JSON with key 'topics' containing an array of objects: "
            "{'topic': str, 'explanation': str, 'importance': 'Critical'|'High'|'Medium', 'related_concepts': [str]}."
        )
        prompt = f"Study Material:\n{truncate_text(material, 15000)}"

        try:
            raw = await self._call_openai_json(prompt, system_prompt)
            topics_data = raw.get("topics", [])
            return [ImportantTopicResult(**t) for t in topics_data]
        except Exception as exc:
            logger.warning(f"OpenAI topics call failed ({exc}). Using fallback.")
            return await self.fallback.generate_topics(material)

    async def generate_question_paper(
        self, material: str, config: QuestionPaperConfig
    ) -> List[QuestionResult]:
        if not self.client:
            return await self.fallback.generate_question_paper(material, config)

        system_prompt = (
            f"Generate a question paper of {config.num_questions} questions for university students. "
            f"Question types: '{config.question_type}', difficulty: '{config.difficulty}', total marks: {config.total_marks}. "
            "Return JSON with key 'questions' containing an array of objects: "
            "{'question_number': int, 'question_text': str, 'question_type': str, 'marks': int, 'difficulty': str, "
            "'options': [str] (4 items for MCQ, empty for others), 'correct_answer': str, 'explanation': str}."
        )
        prompt = f"Study Material:\n{truncate_text(material, 15000)}"

        try:
            raw = await self._call_openai_json(prompt, system_prompt)
            questions_data = raw.get("questions", [])
            return [QuestionResult(**q) for q in questions_data]
        except Exception as exc:
            logger.warning(f"OpenAI question paper call failed ({exc}). Using fallback.")
            return await self.fallback.generate_question_paper(material, config)
