"""Typed contracts for recommendation planning and evidence."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RagToolPlan(BaseModel):
    """RAG retrieval requests planned by the LLM."""

    rag_requests: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("rag_requests")
    @classmethod
    def clean_requests(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]


class SearchToolPlan(BaseModel):
    """Search requests planned by the LLM."""

    search_queries: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("search_queries")
    @classmethod
    def clean_queries(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]


class NeededTools(BaseModel):
    """Tool set the planner wants the backend to execute."""

    rag: RagToolPlan | None = None
    search: SearchToolPlan | None = None

    def normalized(self) -> "NeededTools | None":
        rag = self.rag if self.rag and self.rag.rag_requests else None
        search = self.search if self.search and self.search.search_queries else None
        if rag is None and search is None:
            return None
        return NeededTools(rag=rag, search=search)


class RecommendationPlan(BaseModel):
    """Strict JSON response from the planner LLM."""

    model_config = ConfigDict(extra="forbid")

    response_text: str = ""
    needed_tools: NeededTools | None = None

    def normalized(self) -> "RecommendationPlan":
        return RecommendationPlan(
            response_text=self.response_text.strip(),
            needed_tools=self.needed_tools.normalized() if self.needed_tools else None,
        )


class RecommendationEvidence(BaseModel):
    """Retrieved item passed to the finalizer model and returned as tool result."""

    source: str
    query: str
    title: str | None = None
    url: str | None = None
    text: str
    score: float | None = None
    metadata: dict = Field(default_factory=dict)

    def compact(self, max_chars: int = 1600) -> dict:
        text = self.text.strip()
        if len(text) > max_chars:
            text = text[:max_chars].rsplit(" ", 1)[0].rstrip() + "..."
        return {
            "source": self.source,
            "query": self.query,
            "title": self.title,
            "url": self.url,
            "text": text,
            "score": self.score,
            "metadata": self.metadata,
        }


RECOMMENDATION_PLAN_JSON_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["response_text", "needed_tools"],
    "properties": {
        "response_text": {"type": "string"},
        "needed_tools": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["rag", "search"],
                    "properties": {
                        "rag": {
                            "anyOf": [
                                {"type": "null"},
                                {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["rag_requests"],
                                    "properties": {
                                        "rag_requests": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "maxItems": 5,
                                        }
                                    },
                                },
                            ]
                        },
                        "search": {
                            "anyOf": [
                                {"type": "null"},
                                {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["search_queries"],
                                    "properties": {
                                        "search_queries": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "maxItems": 5,
                                        }
                                    },
                                },
                            ]
                        },
                    },
                },
            ]
        },
    },
}

