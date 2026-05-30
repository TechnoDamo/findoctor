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


class UserDataQuery(BaseModel):
    """A single query against the user's financial database."""

    model_config = ConfigDict(extra="forbid")

    domain: str
    filters: dict = Field(default_factory=dict)
    aggregation: str = "none"
    aggregation_field: str | None = None
    group_by_field: str | None = None
    sort_field: str | None = None
    sort_order: str = "desc"
    limit: int = 50


class UserDataToolPlan(BaseModel):
    """Multiple user data queries the planner wants to execute."""

    model_config = ConfigDict(extra="forbid")

    queries: list[UserDataQuery] = Field(min_length=1, max_length=10)


class UserDataToolResult(BaseModel):
    """Result of a single user data tool execution."""

    domain: str
    query: UserDataQuery
    data: list[dict] | dict
    count: int
    error: str | None = None


class NeededTools(BaseModel):
    """Tool set the planner wants the backend to execute."""

    rag: RagToolPlan | None = None
    search: SearchToolPlan | None = None
    user_data: UserDataToolPlan | None = None

    def normalized(self) -> "NeededTools | None":
        rag = self.rag if self.rag and self.rag.rag_requests else None
        search = self.search if self.search and self.search.search_queries else None
        user_data = self.user_data if self.user_data and self.user_data.queries else None
        if rag is None and search is None and user_data is None:
            return None
        return NeededTools(rag=rag, search=search, user_data=user_data)


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


USER_DATA_DOMAINS = [
    "accounts", "transactions", "transfers", "assets",
    "liabilities", "liability_payments", "recurring_transactions",
    "goals", "tags", "dashboard_summary", "cash_flow",
    "net_worth", "snapshots", "account_types", "asset_types",
    "liability_types", "provider_types", "categories",
    "merchants", "financial_institutions", "conversation_history",
]

VALID_AGGREGATIONS = {"none", "sum", "count", "avg", "min", "max", "group_by", "top_n"}

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
                    "required": ["rag", "search", "user_data"],
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
                        "user_data": {
                            "anyOf": [
                                {"type": "null"},
                                {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["queries"],
                                    "properties": {
                                        "queries": {
                                            "type": "array",
                                            "minItems": 1,
                                            "maxItems": 10,
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": False,
                                                "required": ["domain"],
                                                "properties": {
                                                    "domain": {"type": "string", "enum": USER_DATA_DOMAINS},
                                                    "filters": {"type": "object", "default": {}},
                                                    "aggregation": {"type": "string", "enum": sorted(VALID_AGGREGATIONS), "default": "none"},
                                                    "aggregation_field": {"type": "string"},
                                                    "group_by_field": {"type": "string"},
                                                    "sort_field": {"type": "string"},
                                                    "sort_order": {"type": "string", "enum": ["asc", "desc"], "default": "desc"},
                                                    "limit": {"type": "integer", "minimum": 1, "maximum": 250, "default": 50},
                                                },
                                            },
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

