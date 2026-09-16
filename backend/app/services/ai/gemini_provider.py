import json
import logging
from typing import List, Dict, Any
from google import genai
from google.genai import types

from app.services.ai.base import BaseAIProvider
from app.services.ai.fallback_provider import FallbackAIProvider
from app.schemas.summary import SummaryResult
from app.schemas.topic import ImportantTopicResult
from app.schemas.question_paper import QuestionPaperConfig, QuestionResult
from app.utils.text_processing import truncate_text

logger = logging.getLogger("studygen.ai.gemini")

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str = "", model: str = "gemini-2.5-flash"):
        self.api_key = api_key.strip()
        self.model = model.strip() or "gemini-2.5-flash"
        self.fallback = FallbackAIProvider()
        is_real_key = bool(self.api_key and self.api_key != "your_gemini_api_key_here")
        self.client = genai.Client(api_key=self.api_key) if is_real_key else None

    @property
    def provider_name(self) -> str:
        return f"gemini:{self.model}"

    async def _call_gemini_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        if not self.client:
            raise ValueError("GEMINI_API_KEY is not configured in environment.")

        config = types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            system_instruction=system_prompt + "\nReturn ONLY valid JSON matching the requested schema."
        )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )

        raw_text = response.text or "{}"
        return json.loads(raw_text)

    async def generate_summary(self, material: str) -> SummaryResult:
        if not self.client:
            logger.info("Gemini API key not configured; using heuristic fallback.")
            return await self.fallback.generate_summary(material)

        system_prompt = (
            "You are an expert academic tutor. Analyze the provided study material and generate a structured summary. "
            "Extract ONLY factual information present in the material without fabricating external details. "
            "Return JSON with keys: "
            "'summary' (string: detailed overview), "
            "'key_concepts' (array of strings), "
            "'important_topics' (array of strings), "
            "'quick_revision' (array of strings, concise bullet points)."
        )
        prompt = f"Study Material:\n{truncate_text(material, 15000)}"

        try:
            raw = await self._call_gemini_json(prompt, system_prompt)
            return SummaryResult(
                summary=raw.get("summary", ""),
                key_concepts=raw.get("key_concepts", []),
                important_topics=raw.get("important_topics", []),
                quick_revision=raw.get("quick_revision", [])
            )
        except Exception as exc:
            logger.warning(f"Gemini summary generation failed ({exc}). Using fallback.")
            return await self.fallback.generate_summary(material)

    async def generate_topics(self, material: str) -> List[ImportantTopicResult]:
        if not self.client:
            return await self.fallback.generate_topics(material)

        system_prompt = (
            "Extract high-priority study topics from the provided material for exam preparation. "
            "Return JSON with key 'topics', which is an array of objects. "
            "Each object must have: 'topic' (string), 'explanation' (string), 'importance' ('Critical'|'High'|'Medium'), 'related_concepts' (array of strings)."
        )
        prompt = f"Study Material:\n{truncate_text(material, 15000)}"

        try:
            raw = await self._call_gemini_json(prompt, system_prompt)
            topics_data = raw.get("topics", [])
            return [ImportantTopicResult(**t) for t in topics_data]
        except Exception as exc:
            logger.warning(f"Gemini topics generation failed ({exc}). Using fallback.")
            return await self.fallback.generate_topics(material)

    async def generate_question_paper(
        self, material: str, config: QuestionPaperConfig
    ) -> List[QuestionResult]:
        if not self.client:
            return await self.fallback.generate_question_paper(material, config)

        system_prompt = (
            f"You are a university exam creator. Create a question paper of exactly {config.num_questions} questions "
            f"strictly from the provided study material. Question types should be '{config.question_type}' and difficulty '{config.difficulty}'. "
            f"Total marks across the paper: {config.total_marks}. "
            "Return JSON with key 'questions', an array of objects. "
            "Each object MUST contain: 'question_number' (int), 'question_text' (str), 'question_type' (str: MCQ, Short Answer, or Long Answer), "
            "'marks' (int), 'difficulty' (str), 'options' (array of 4 strings for MCQ, empty array otherwise), "
            "'correct_answer' (str), 'explanation' (str with reasoning from the text)."
        )
        prompt = f"Study Material:\n{truncate_text(material, 15000)}"

        try:
            raw = await self._call_gemini_json(prompt, system_prompt)
            questions_data = raw.get("questions", [])
            return [QuestionResult(**q) for q in questions_data]
        except Exception as exc:
            logger.warning(f"Gemini question paper generation failed ({exc}). Using fallback.")
            return await self.fallback.generate_question_paper(material, config)
