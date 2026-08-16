"""
backend/ingestion/article.py

Extracts clean, readable text from an article URL — strips ads, nav,
comments, and other page chrome, leaving just the actual content.

Consistent with youtube.py: everything is standardized to English before
it reaches the embedding pipeline, regardless of source language.
"""

import sys
import requests
import trafilatura
from dataclasses import dataclass
from urllib.parse import urlparse

# Windows terminals default to cp1252, which can't print non-English text.
# Force UTF-8 output so this doesn't crash (same fix as youtube.py).
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


@dataclass
class ArticleContent:
    url: str
    title: str
    site_name: str
    text: str          # clean extracted body text, English
    language: str       # original detected language (e.g. 'en', 'hi')


def fetch_html(url: str) -> str:
    """
    Downloads the raw HTML for a URL.
    Uses a real User-Agent since many sites block default request headers.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.text


def extract_clean_text(html: str, url: str) -> dict:
    """
    Runs trafilatura's extraction — strips nav/ads/comments, keeps the
    actual article body. Also pulls metadata (title, site name, language)
    in the same pass.
    """
    result = trafilatura.extract(
        html,
        url=url,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        include_tables=False,
    )

    if not result:
        raise ValueError(f"Could not extract readable content from: {url}")

    import json
    data = json.loads(result)

    return {
        "title": data.get("title") or "Untitled",
        "site_name": data.get("sitename") or urlparse(url).netloc,
        "text": data.get("text", ""),
        "language": data.get("language") or "unknown",
    }


def translate_to_english(text: str, source_language: str) -> str:
    """
    Translates non-English article text to English, matching the same
    "everything standardized to English" decision made for YouTube content.

    Uses deep-translator (Google Translate backend) since trafilatura has
    no built-in translation. Chunks the text to stay under the per-request
    character limit of most free translation APIs (~4500 chars).
    """
    if source_language == "en" or not text.strip():
        return text

    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        print(
            "Warning: deep-translator not installed — skipping translation, "
            "storing original-language text instead. Run: "
            "pip install deep-translator"
        )
        return text

    translator = GoogleTranslator(source="auto", target="en")

    # Split into ~4000-char chunks so we don't hit API length limits,
    # breaking on paragraph boundaries where possible.
    chunk_size = 4000
    paragraphs = text.split("\n")
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) > chunk_size:
            chunks.append(current)
            current = para
        else:
            current += "\n" + para if current else para
    if current:
        chunks.append(current)

    translated_chunks = []
    for chunk in chunks:
        try:
            translated_chunks.append(translator.translate(chunk))
        except Exception as e:
            print(f"Warning: translation failed for a chunk ({e}), keeping original text")
            translated_chunks.append(chunk)

    return "\n".join(translated_chunks)


def process_article_url(url: str) -> ArticleContent:
    """
    Main entry point — call this from the ingestion pipeline.
    Returns a fully populated ArticleContent object, text guaranteed English.
    """
    html = fetch_html(url)
    extracted = extract_clean_text(html, url)

    english_text = translate_to_english(extracted["text"], extracted["language"])

    return ArticleContent(
        url=url,
        title=extracted["title"],
        site_name=extracted["site_name"],
        text=english_text,
        language=extracted["language"],
    )


# --- Quick manual test ---
# Run directly: python article.py
if __name__ == "__main__":
    test_url = input("Paste an article URL to test: ").strip()
    content = process_article_url(test_url)
    print(f"\nTitle: {content.title}")
    print(f"Site: {content.site_name}")
    print(f"Detected language: {content.language}")
    print(f"Text length: {len(content.text)} characters")
    print(f"\nFirst 300 chars:\n{content.text[:300]}...")
