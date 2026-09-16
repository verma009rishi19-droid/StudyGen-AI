import json
import logging
import httpx
from typing import List, Dict, Any

from app.services.ai.base import BaseAIProvider
from app.services.ai.fallback_provider import FallbackAIProvider
from app.schemas.summary import SummaryResult
from app.schemas.topic import ImportantTopicResult
from app.schemas.question_paper import QuestionPaperConfig, QuestionResult
from app.utils.text_processing import truncate_text

logger = logging.getLogger("studygen.ai.ollama")

class OllamaProvider(BaseAIProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.fallback = FallbackAIProvider()

    @property
    def provider_name(self) -> str:
        return f"ollama:{self.model}"

    async def _call_ollama_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Calls the local Ollama chat API with JSON mode enabled."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt + "\nReturn ONLY valid JSON matching the requested structure. Do not wrap in markdown quotes."},
                {"role": "user", "content": prompt}
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }

        timeout = httpx.Timeout(connect=2.5, read=60.0, write=10.0, pool=5.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {response.text}")
                data = response.json()
                content = data.get("message", {}).get("content", "{}")
                return json.loads(content)
        except Exception as exc:
            logger.warning(f"Ollama call failed or daemon offline ({exc}). Using internal heuristic fallback.")
            raise exc

    async def generate_summary(self, material: str) -> SummaryResult:
        system_prompt = (
            "You are an expert academic tutor. Analyze the provided study material and generate a structured summary. "
            "Extract ONLY factual information present in the material without fabricating external details. "
            "Return JSON with keys: "
            "'summary' (string: detailed overview), "
            "'key_concepts' (array of strings), "
            "'important_topics' (array of strings), "
            "'quick_revision' (array of strings, concise bullet points)."
        )
        prompt = f"Study Material:\n{truncate_text(material, 12000)}"

        try:
            raw = await self._call_ollama_json(prompt, system_prompt)
            return SummaryResult(
                summary=raw.get("summary", ""),
                key_concepts=raw.get("key_concepts", []),
                important_topics=raw.get("important_topics", []),
                quick_revision=raw.get("quick_revision", [])
            )
        except Exception:
            return await self.fallback.generate_summary(material)

    async def generate_topics(self, material: str) -> List[ImportantTopicResult]:
        system_prompt = (
            "Extract high-priority study topics from the provided material for exam preparation. "
            "Return JSON with key 'topics', which is an array of objects. "
            "Each object must have: 'topic' (string), 'explanation' (string), 'importance' ('Critical'|'High'|'Medium'), 'related_concepts' (array of strings)."
        )
        prompt = f"Study Material:\n{truncate_text(material, 12000)}"

        try:
            raw = await self._call_ollama_json(prompt, system_prompt)
            topics_data = raw.get("topics", [])
            return [ImportantTopicResult(**t) for t in topics_data]
        except Exception:
            return await self.fallback.generate_topics(material)

    async def generate_question_paper(
        self, material: str, config: QuestionPaperConfig
    ) -> List[QuestionResult]:
        system_prompt = (
            f"You are a university exam creator. Create a question paper of exactly {config.num_questions} questions "
            f"strictly from the provided study material. Question types should be '{config.question_type}' and difficulty '{config.difficulty}'. "
            f"Total marks across the paper: {config.total_marks}. "
            "Return JSON with key 'questions', an array of objects. "
            "Each object MUST contain: 'question_number' (int), 'question_text' (str), 'question_type' (str: MCQ, Short Answer, or Long Answer), "
            "'marks' (int), 'difficulty' (str), 'options' (array of 4 strings for MCQ, empty array otherwise), "
            "'correct_answer' (str), 'explanation' (str with reasoning from the text)."
        )
        prompt = f"Study Material:\n{truncate_text(material, 12000)}"

        try:
            raw = await self._call_ollama_json(prompt, system_prompt)
            questions_data = raw.get("questions", [])
            return [QuestionResult(**q) for q in questions_data]
        except Exception:
            return await self.fallback.generate_question_paper(material, config)
