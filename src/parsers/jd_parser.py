"""Parse job descriptions from uploads or URLs."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .resume_parser import extract_text_from_docx, extract_text_from_pdf, _normalize_whitespace


def extract_text_from_upload(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        text = extract_text_from_pdf(data)
    elif suffix == ".docx":
        text = extract_text_from_docx(data)
    elif suffix in {".txt", ".md"}:
        text = _normalize_whitespace(data.decode("utf-8", errors="ignore"))
    else:
        raise ValueError("Unsupported JD file type. Use PDF, DOCX, or TXT.")

    if not text:
        raise ValueError("Could not extract text from the job description file.")
    return text


def extract_jd_from_bytes(filename: str, data: bytes) -> str:
    return extract_text_from_upload(filename, data)


def _visible_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "svg"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return _normalize_whitespace(text)


def extract_jd_from_url(url: str, timeout: float = 20.0) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Enter a valid http(s) job posting URL.")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; AIResumeAnalyzer/1.0; "
            "+https://github.com/example/ai-resume-analyzer)"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError(
            "Could not fetch that URL (blocked or unreachable). "
            "Paste the job description text instead."
        ) from exc

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type and "text" not in content_type:
        raise ValueError("URL did not return HTML/text content. Paste the JD instead.")

    text = _visible_text_from_html(response.text)
    if len(text) < 80:
        raise ValueError(
            "Scraped page had too little text (likely blocked). "
            "Paste the job description manually."
        )
    # Cap extremely long pages for LLM context
    return text[:20000]
