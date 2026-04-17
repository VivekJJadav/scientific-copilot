from __future__ import annotations

from io import BytesIO

import httpx
import structlog

logger = structlog.get_logger(__name__)


async def fetch_pdf_text(pdf_url: str) -> tuple[str | None, list[str], str]:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        logger.warning("pdf_parser_unavailable", error=str(exc))
        return None, [], "abstract"

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
    except Exception as exc:
        logger.warning("pdf_fetch_failed", pdf_url=pdf_url, error=str(exc))
        return None, [], "abstract"

    try:
        reader = PdfReader(BytesIO(response.content))
        pages = [page.extract_text() or "" for page in reader.pages]
        full_text = "\n".join(part.strip() for part in pages if part and part.strip()).strip()
        if full_text:
            full_text = full_text.replace("\x00", "")
    except Exception as exc:
        logger.warning("pdf_parse_failed", pdf_url=pdf_url, error=str(exc))
        return None, [], "abstract"

    if not full_text:
        return None, [], "abstract"

    chunks = chunk_text(full_text)
    return full_text, chunks, "pdf"


def chunk_text(text: str, chunk_size: int = 2500, overlap: int = 250) -> list[str]:
    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])
        if end >= length:
            break
        start = max(end - overlap, start + 1)

    return chunks
