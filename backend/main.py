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
    URLRequest,
    HighlightRequest,
    VerifySessionRequest
)
from extractor import extract_from_html, verify_locators_in_html
from playwright_service import capture_page_data_sync, browser_manager

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
    return {"status": "ok"}

# --- Persistent Session Endpoints ---

@app.post("/v1/session/start")
async def start_session(payload: URLRequest):
    try:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, browser_manager.start_session, payload.url)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/session/capture", response_model=ExtractResponse)
async def capture_session():
    try:
        loop = asyncio.get_running_loop()
        extracted = await loop.run_in_executor(None, browser_manager.capture_current_state)
        return ExtractResponse.model_validate(extracted)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/session/verify")
async def verify_session(payload: VerifySessionRequest):
    try:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, browser_manager.verify_session_locators, payload.elements)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/session/stop")
async def stop_session():
    try:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, browser_manager.stop_session)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/session/highlight")
async def highlight_session_element(payload: HighlightRequest):
    try:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(
            None, 
            browser_manager.highlight_element, 
            payload.strategy, 
            payload.value, 
            payload.internal_xpath
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Standard Endpoints ---

@app.post("/v1/locators/extract", response_model=ExtractResponse)
def extract_locators(payload: ExtractRequest) -> ExtractResponse:
    extracted = extract_from_html(payload.html)
    return ExtractResponse.model_validate(extracted)

@app.post("/v1/locators/extract-url", response_model=ExtractResponse)
async def extract_locators_from_url(payload: URLRequest) -> ExtractResponse:
    try:
        loop = asyncio.get_running_loop()
        extracted = await loop.run_in_executor(None, capture_page_data_sync, payload.url)
        return ExtractResponse.model_validate(extracted)
    except Exception as e:
        logger.error(f"URL Extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/locators/verify", response_model=VerifyResponse)
def verify_locators(payload: VerifyRequest) -> VerifyResponse:
    results = verify_locators_in_html(payload.html, payload.elements)
    return VerifyResponse.model_validate(results)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
