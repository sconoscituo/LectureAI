from abc import abstractmethod
from typing import Any, Dict, List
from app.domain.ports.base_service import AbstractService


class AbstractLectureService(AbstractService):
    @abstractmethod
    async def transcribe_audio(self, audio_path: str) -> str: ...
    @abstractmethod
    async def summarize_lecture(self, transcript: str) -> Dict[str, Any]: ...
    @abstractmethod
    async def generate_quiz(self, transcript: str, num_questions: int = 5) -> List[Dict[str, Any]]: ...
