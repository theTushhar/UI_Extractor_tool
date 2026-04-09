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



