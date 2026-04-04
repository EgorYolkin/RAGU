from __future__ import annotations

from src.domain.models import Candidate
from src.retrieve.service import RetrievalService


class QueryService:
    def __init__(self, retrieval_service: RetrievalService) -> None:
        self.retrieval_service = retrieval_service

    def retrieve(self, query: str) -> list[Candidate]:
        return self.retrieval_service.retrieve(query)
