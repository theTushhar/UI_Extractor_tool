from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from playwright.sync_api import sync_playwright, Browser, Page
from pydantic import BaseModel
import asyncio
import logging
import time

from utils import get_clean_dom
from locator_strategy import generate_locators
from validator import validate_locators


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

browser_instance: Browser | None = None
page_instance: Page | None = None
playwright_instance = None


def truncate(value: str, limit: int = 120) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit - 3]}..."


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    logger.info("HTTP %s %s started", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "HTTP %s %s crashed after %.2fms",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "HTTP %s %s completed with %s in %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


def init_playwright():
    global playwright_instance, browser_instance, page_instance
    logger.info("Initializing Playwright")
    if playwright_instance is None:
        playwright_instance = sync_playwright().start()
        try:
            browser_instance = playwright_instance.chromium.launch(headless=True)
            logger.info("Browser launched successfully in headless mode")
        except Exception as exc:
            logger.exception("Failed to launch browser")
            cleanup_playwright()
            raise RuntimeError(
                "Failed to launch Playwright browser. If this is a fresh setup, run "
                "`python -m playwright install chromium` inside the backend environment."
            ) from exc
        context = browser_instance.new_context()
        page_instance = context.new_page()
        logger.info("Playwright initialized successfully")
    else:
        logger.debug("Reusing existing Playwright instance")


def cleanup_playwright():
    global playwright_instance, browser_instance, page_instance
    logger.info("Cleaning up Playwright resources")
    if browser_instance:
        browser_instance.close()
    if playwright_instance:
        playwright_instance.stop()
    browser_instance = None
    page_instance = None
    playwright_instance = None


class OpenBrowserRequest(BaseModel):
    url: str


class ScanPageRequest(BaseModel):
    goal: str
    api_key: str
    model: str


class HighlightElementRequest(BaseModel):
    selector: str


@app.post("/open-browser")
async def open_browser(request: OpenBrowserRequest):
    logger.info("Received open-browser request for URL: %s", truncate(request.url))
    global browser_instance, page_instance

    def _open_browser_sync(url: str):
        global browser_instance, page_instance
        if browser_instance and page_instance:
            logger.info("Browser already open, navigating to: %s", truncate(url))
            page_instance.goto(url)
            logger.debug("Navigation completed, current page URL: %s", page_instance.url)
            return {"status": "Navigated", "url": page_instance.url}

        logger.info("Launching browser for first navigation")
        try:
            init_playwright()
            logger.info("Navigating to initial URL: %s", truncate(url))
            page_instance.goto(url)
            logger.debug("Initial navigation completed, current page URL: %s", page_instance.url)
            return {"status": "Browser Opened", "url": page_instance.url}
        except Exception:
            logger.exception("Failed during open-browser flow")
            raise

    try:
        result = await asyncio.get_event_loop().run_in_executor(None, _open_browser_sync, request.url)
        logger.info("Open browser result: %s", result)
        return result
    except Exception as exc:
        logger.error("Open browser error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/close-browser")
async def close_browser():
    logger.info("Received close-browser request")

    def _close_browser_sync():
        logger.info("Closing browser")
        cleanup_playwright()
        return {"status": "Closed"}

    try:
        result = await asyncio.get_event_loop().run_in_executor(None, _close_browser_sync)
        logger.info("Close browser completed: %s", result)
        return result
    except Exception as exc:
        logger.exception("Close browser error")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/scan-page")
async def scan_page(request: ScanPageRequest):
    logger.info(
        "Received scan-page request | goal=%s | model=%s | api_key_present=%s",
        truncate(request.goal, 80),
        request.model,
        bool(request.api_key),
    )

    def _scan_page_sync(goal: str, api_key: str, model: str):
        global page_instance
        if not page_instance:
            logger.error("Scan requested without an open browser")
            raise Exception("Browser is not open.")

        try:
            logger.info("Starting scan pipeline")
            html_content = page_instance.content()
            logger.debug("Fetched HTML content length: %s", len(html_content))
            clean_dom = get_clean_dom(html_content)
            logger.debug("Clean DOM length: %s", len(clean_dom))

            candidates = generate_locators(clean_dom, goal, api_key, model)
            logger.info("Generated %s locator candidates", len(candidates))
            final_report = validate_locators(page_instance, candidates)
            logger.info("Validated %s locator candidates", len(final_report))
            logger.debug("Validation statuses: %s", [item.get("status") for item in final_report])
            return final_report
        except Exception:
            logger.exception("Scan page pipeline failed")
            raise

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            _scan_page_sync,
            request.goal,
            request.api_key,
            request.model,
        )
        logger.info("Scan page completed successfully")
        return result
    except Exception as exc:
        logger.error("Scan page request failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/highlight-element")
async def highlight_element(request: HighlightElementRequest):
    logger.info("Received highlight-element request for selector: %s", truncate(request.selector))

    def _highlight_element_sync(selector: str):
        global page_instance
        if not page_instance:
            logger.error("Highlight requested without an open browser")
            raise Exception("Browser is not open.")

        try:
            result = page_instance.evaluate(
                """(selector) => {
                const styleId = 'ai-agent-highlight-style';
                if (!document.getElementById(styleId)) {
                    const style = document.createElement('style');
                    style.id = styleId;
                    style.innerHTML = `
                        .ai-agent-highlight {
                            outline: 3px solid #ff0000 !important;
                            z-index: 10000 !important;
                            transition: all 0.3s ease !important;
                        }
                    `;
                    document.head.appendChild(style);
                }

                document.querySelectorAll('.ai-agent-highlight').forEach((el) => {
                    el.classList.remove('ai-agent-highlight');
                });

                const element = document.querySelector(selector);
                if (element) {
                    element.classList.add('ai-agent-highlight');
                    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    return { status: 'Highlighted' };
                }
                return { status: 'Not Found' };
            }""",
                selector,
            )
            logger.info("Highlight result: %s", result)
            return result
        except Exception:
            logger.exception("Highlight element failed")
            raise

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            _highlight_element_sync,
            request.selector,
        )
        logger.info("Highlight element completed")
        return result
    except Exception as exc:
        logger.error("Highlight request failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/")
async def read_root():
    logger.debug("Health check requested")
    return {"message": "FastAPI backend is running!"}
