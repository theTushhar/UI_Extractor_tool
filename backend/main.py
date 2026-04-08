import logging
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from schemas import (
    ExtractRequest, 
    ExtractResponse, 
    PathBasedTestCaseRequest, 
    PathBasedTestCaseResponse
)
from extractor import extract_from_html, generate_path_based_test_cases

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="UI Locator Tool", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Simplified for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "UI Locator Backend is running!"}

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/v1/locators/extract", response_model=ExtractResponse)
def extract_locators(payload: ExtractRequest) -> ExtractResponse:
    request_id = str(uuid.uuid4())[:8]
    logger.info("Request started: id=%s html_len=%d", request_id, len(payload.html))
    
    extracted = extract_from_html(payload.html)
    
    logger.info(
        "Request completed: id=%s elements=%d stable=%d",
        request_id,
        extracted.get("total_elements", 0),
        extracted.get("stable_elements", 0),
    )
    return ExtractResponse.model_validate(extracted)

@app.post("/v1/testcases/path-based", response_model=PathBasedTestCaseResponse)
def generate_path_based(payload: PathBasedTestCaseRequest) -> PathBasedTestCaseResponse:
    request_id = str(uuid.uuid4())[:8]
    logger.info(
        "Path-based generation started: id=%s requirement_len=%d user_prompt_len=%d",
        request_id,
        len(payload.requirement),
        len(payload.user_prompt),
    )
    generated = generate_path_based_test_cases(
        requirement=payload.requirement,
        user_prompt=payload.user_prompt,
        max_paths=payload.max_paths,
    )
    logger.info(
        "Path-based generation completed: id=%s paths=%d test_cases=%d",
        request_id,
        len(generated.get("unique_paths", [])),
        len(generated.get("test_case_summary", [])),
    )
    return PathBasedTestCaseResponse.model_validate(generated)
