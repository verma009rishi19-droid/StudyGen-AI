from abc import ABC, abstractmethod
from typing import List
from app.schemas.summary import SummaryResult
from app.schemas.topic import ImportantTopicResult
from app.schemas.question_paper import QuestionPaperConfig, QuestionResult

class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider, e.g. 'ollama:llama3' or 'openai:gpt-4o-mini'."""
        pass

    @abstractmethod
    async def generate_summary(self, material: str) -> SummaryResult:
        """Generates structured summary, key concepts, important topics, and quick revision points."""
        pass

    @abstractmethod
    async def generate_topics(self, material: str) -> List[ImportantTopicResult]:
        """Extracts high-priority topics with explanations and related concepts."""
        pass

    @abstractmethod
    async def generate_question_paper(
        self, material: str, config: QuestionPaperConfig
    ) -> List[QuestionResult]:
        """Generates questions adhering to the specified paper configuration."""
        pass
