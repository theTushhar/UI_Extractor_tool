from typing import Any, Literal
from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    html: str = Field(..., min_length=1, description="Raw HTML content")


class URLRequest(BaseModel):
    url: str = Field(..., description="Target URL to extract from")


class LocatorCandidate(BaseModel):
    rank: int
    strategy: str
    value: str
    unique: bool
    score: int


class RecommendedLocator(BaseModel):
    rank: int
    strategy: str
    value: str
    score: int
    reason: str


class ExtractedElement(BaseModel):
    tag: str
    element_name: str
    mode: Literal["Input", "Output", "UserAction", "Unknown"] = "Unknown"
    element_type: str
    absolute_xpath: str
    attributes: dict[str, str]
    recommended_locator: RecommendedLocator
    locators: list[LocatorCandidate]


class ExtractResponse(BaseModel):
    page_name: str
    total_elements: int
    stable_elements: int
    elements: list[ExtractedElement]
    url: str | None = None
    screenshot: str | None = None


class VerifyRequest(BaseModel):
    html: str
    elements: list[dict]


class VerifyResponse(BaseModel):
    verified_elements: list[dict]
    summary: dict[str, int]



