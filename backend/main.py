import asyncio
import sys
import logging
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Fix for Windows asyncio NotImplementedError
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from schemas import (
    ExtractRequest, 
    ExtractResponse,
    VerifyRequest,
    VerifyResponse,
    URLRequest
)
from extractor import extract_from_html, verify_locators_in_html
from playwright_service import capture_page_data_sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="UI Locator Tool", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "UI Locator Backend is running!"}

@app.get("/health")
def health() -> dict:
    loop = asyncio.get_event_loop()
    return {"status": "ok", "loop": type(loop).__name__}

@app.post("/v1/locators/extract", response_model=ExtractResponse)
def extract_locators(payload: ExtractRequest) -> ExtractResponse:
    request_id = str(uuid.uuid4())[:8]
    logger.info("Request started: id=%s html_len=%d", request_id, len(payload.html))
    extracted = extract_from_html(payload.html)
    return ExtractResponse.model_validate(extracted)

@app.post("/v1/locators/extract-url", response_model=ExtractResponse)
async def extract_locators_from_url(payload: URLRequest) -> ExtractResponse:
    request_id = str(uuid.uuid4())[:8]
    logger.info("URL Extraction started: id=%s url=%s", request_id, payload.url)
    
    try:
        # Run sync Playwright in a thread to bypass Windows async issues
        loop = asyncio.get_running_loop()
        extracted = await loop.run_in_executor(None, capture_page_data_sync, payload.url)
        
        logger.info(
            "URL Extraction completed: id=%s elements=%d",
            request_id,
            extracted.get("total_elements", 0),
        )
        return ExtractResponse.model_validate(extracted)
    except Exception as e:
        logger.error("URL Extraction failed: id=%s error=%s", request_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/locators/verify", response_model=VerifyResponse)
def verify_locators(payload: VerifyRequest) -> VerifyResponse:
    results = verify_locators_in_html(payload.html, payload.elements)
    return VerifyResponse.model_validate(results)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
