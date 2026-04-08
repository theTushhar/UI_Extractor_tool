from typing import Any, Literal
from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    html: str = Field(..., min_length=1, description="Raw HTML content")


class LocatorCandidate(BaseModel):
    rank: int
    strategy: str
    value: str
    unique: bool
    score: int


class RecommendedLocator(BaseModel):
    strategy: str
    value: str
    score: int
    reason: str


class ExtractedElement(BaseModel):
    tag: str
    element_name: str
    mode: Literal["Input", "Output", "UserAction", "Unknown"] = "Unknown"
    element_type: str
    attributes: dict[str, str]
    recommended_locator: RecommendedLocator
    locators: list[LocatorCandidate]


class ExtractResponse(BaseModel):
    page_name: str
    total_elements: int
    stable_elements: int
    elements: list[ExtractedElement]


class PathBasedTestCaseRequest(BaseModel):
    requirement: str = Field(..., min_length=1, description="Requirement text provided by user.")
    user_prompt: str = Field(..., min_length=1, description="Prompt that drives the generation intent.")
    max_paths: int = Field(
        default=32,
        ge=1,
        le=256,
        description="Safety cap for path combinations when many required fields are present.",
    )


class PathBasedTestCaseResponse(BaseModel):
    intent: dict[str, str]
    pseudo_code: str
    unique_paths: list[dict[str, Any]]
    test_case_summary: list[dict[str, str]]
    detailed_test_cases: list[dict[str, Any]]
    path_test_case_correlation: list[dict[str, str]]
    notes: list[str] = Field(default_factory=list)
