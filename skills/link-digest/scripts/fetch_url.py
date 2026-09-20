#!/usr/bin/env python3
"""Fetch a URL and return readable article text plus outbound links as JSON.

Usage:
    python3 fetch_url.py URL [--max-chars 24000] [--no-reader] [--pretty]

Design notes:
  - Fetching goes through curl so gzip/brotli, redirects and cookies behave like a browser.
  - x.com / twitter.com use the public syndication + oembed endpoints, since the normal
    page body is rendered client-side.
  - When extraction yields too little text, a text-extraction reader proxy is used as a
    last resort (disable with --no-reader; the page URL is then sent to that third party).
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import os
import re
import subprocess
import sys
import tempfile
from urllib.parse import urljoin, urlparse

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
READER_PREFIX = "https://r.jina.ai/"
TWEET_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com", "mobile.x.com"}
MIN_USEFUL_TEXT = 400


def run_curl(url: str, timeout: int = 30, accept: str | None = None):
    """Return (status, content_type, final_url, body_bytes)."""
    with tempfile.NamedTemporaryFile(delete=False) as handle:
        body_path = handle.name
    cmd = [
        "curl", "-sSL", "--compressed", "--max-time", str(timeout),
        "-A", BROWSER_UA,
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
        "-w", "%{http_code}\t%{content_type}\t%{url_effective}",
        "-o", body_path,
    ]
    if accept:
        cmd += ["-H", f"Accept: {accept}"]
    cmd.append(url)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    except subprocess.TimeoutExpired:
        return 0, "", url, b""
    meta = (proc.stdout or "").strip().splitlines()
    status, ctype, final_url = 0, "", url
    if meta:
        parts = meta[-1].split("\t")
        if len(parts) == 3:
            try:
                status = int(parts[0])
            except ValueError:
                status = 0
            ctype, final_url = parts[1], parts[2]
    try:
        with open(body_path, "rb") as handle:
            body = handle.read()
    except OSError:
        body = b""
    finally:
        try:
            os.unlink(body_path)
        except OSError:
            pass
    return status, ctype, final_url, body


def decode(body: bytes, ctype: str) -> str:
    charset = "utf-8"
    match = re.search(r"charset=([\w-]+)", ctype or "", re.I)
    if match:
        charset = match.group(1)
    for enc in (charset, "utf-8", "gb18030", "latin-1"):
        try:
            return body.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return body.decode("utf-8", "replace")


def text_from_html(raw: str) -> str:
    body = raw
    for tag in ("script", "style", "noscript", "svg", "template", "form"):
        body = re.sub(rf"(?is)<{tag}\b.*?</{tag}>", " ", body)
    for pattern in (r"(?is)<article\b.*?</article>", r"(?is)<main\b.*?</main>", r"(?is)<body\b.*?</body>"):
        found = re.search(pattern, body)
        if found:
            body = found.group(0)
            break
    body = re.sub(r"(?is)<(br|hr)\s*/?>", "\n", body)
    body = re.sub(r"(?is)</(p|div|li|tr|h[1-6]|section|blockquote|pre)>", "\n", body)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    body = html_mod.unescape(body)
    body = re.sub(r"[ \t\u00a0]+", " ", body)
    lines = [line.strip() for line in body.splitlines()]
    out = [line for line in lines if line]
    return "\n".join(out)


def meta_of(raw: str) -> dict:
    def find(patterns):
        for pattern in patterns:
            match = re.search(pattern, raw, re.I | re.S)
            if match:
                return html_mod.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
        return ""
    return {
        "title": find([r"<meta[^>]+property=['\"]og:title['\"][^>]+content=['\"]([^'\"]+)",
                       r"<meta[^>]+name=['\"]twitter:title['\"][^>]+content=['\"]([^'\"]+)",
                       r"<title[^>]*>(.*?)</title>"]),
        "description": find([r"<meta[^>]+property=['\"]og:description['\"][^>]+content=['\"]([^'\"]+)",
                             r"<meta[^>]+name=['\"]description['\"][^>]+content=['\"]([^'\"]+)"]),
    }


def links_of(raw: str, base: str) -> list[dict]:
    seen, out = set(), []
    for match in re.finditer(r"(?is)<a\b[^>]*href=['\"]([^'\"#]+)['\"][^>]*>(.*?)</a>", raw):
        href, label = match.group(1).strip(), match.group(2)
        if href.lower().startswith(("javascript:", "mailto:", "tel:")):
            continue
        url = urljoin(base, href)
        if not url.lower().startswith(("http://", "https://")) or url in seen:
            continue
        seen.add(url)
        text = html_mod.unescape(re.sub(r"(?s)<[^>]+>", " ", label))
        text = re.sub(r"\s+", " ", text).strip()
        out.append({"url": url, "text": text[:160]})
    return out


def tweet_id(url: str) -> str:
    match = re.search(r"/status(?:es)?/(\d{6,})", url)
    return match.group(1) if match else ""


def tweet_links(text: str, tweet: dict) -> list[dict]:
    """Collect URLs a tweet points at, preferring expanded forms."""
    seen, out = set(), []
    card = tweet.get("twitter_card") or {}
    candidates = []
    if isinstance(card, dict) and card.get("url"):
        candidates.append((card["url"], card.get("title") or "linked page"))
    candidates += [(u, "") for u in re.findall(r"https?://[^\s\"\'<>]+", text or "")]
    for url, label in candidates:
        url = url.rstrip(".,)")
        if url in seen or "t.co/" in url:
            continue
        seen.add(url)
        out.append({"url": url, "text": label})
    quote = tweet.get("quote")
    if isinstance(quote, dict) and quote.get("url"):
        out.append({"url": quote["url"], "text": "quoted tweet"})
    elif isinstance(quote, str) and quote.startswith("http"):
        out.append({"url": quote, "text": "quoted tweet"})
    return out[:20]


def fetch_tweet(url: str, max_chars: int) -> dict | None:
    """X/Twitter via public mirrors first: direct x.com and its CDN are blocked in some networks."""
    tid = tweet_id(url)
    if not tid:
        return None
    errors = []
    bases = [("fxtwitter", "https://api.fxtwitter.com/status/"), ("vxtwitter", "https://api.vxtwitter.com/status/")]
    for name, base in bases:
        status, ctype, final_url, body = run_curl(base + tid, timeout=12, accept="application/json")
        if status != 200 or not body:
            errors.append(f"{name}: http {status}")
            continue
        try:
            data = json.loads(decode(body, ctype))
        except json.JSONDecodeError:
            errors.append(f"{name}: bad JSON")
            continue
        tweet = data.get("tweet") if isinstance(data.get("tweet"), dict) else data
        text = tweet.get("text") or tweet.get("raw_text") or ""
        if not text:
            errors.append(f"{name}: no text")
            continue
        author = tweet.get("author") or {}
        stats = " · ".join(
            f"{key} {tweet[key]}" for key in ("likes", "retweets", "replies", "views")
            if isinstance(tweet.get(key), (int, float))
        )
        parts = [f"{author.get('name', '')} (@{author.get('screen_name', '')}) — {tweet.get('created_at', '')}"]
        if stats:
            parts.append(stats)
        parts += ["", text]
        media = tweet.get("media") or {}
        for photo in (media.get("photos") or []) if isinstance(media, dict) else []:
            parts.append(f"[image] {photo.get('url', '')}")
        if isinstance(quote := tweet.get("quote"), dict) and quote.get("text"):
            parts += ["", f"[quoted] {quote['text']}"]
        return {
            "url": url,
            "final_url": tweet.get("url") or final_url,
            "method": f"twitter-{name}",
            "title": f"Tweet by @{author.get('screen_name', '')}",
            "description": "",
            "text": "\n".join(parts)[:max_chars],
            "links": tweet_links(text, tweet),
            "errors": errors,
        }

    status, ctype, final_url, body = run_curl(
        f"https://cdn.syndication.twimg.com/tweet-result?id={tid}&token=a&lang=en", timeout=12, accept="application/json"
    )
    if status == 200 and body:
        try:
            data = json.loads(decode(body, ctype))
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict) and data.get("text"):
            user = data.get("user") or {}
            parts = [f"{user.get('name', '')} (@{user.get('screen_name', '')}) — {data.get('created_at', '')}", "", data["text"]]
            for photo in data.get("photos") or []:
                parts.append(f"[image] {photo.get('url', '')}")
            return {
                "url": url,
                "final_url": final_url,
                "method": "twitter-syndication",
                "title": f"Tweet by @{user.get('screen_name', '')}",
                "description": "",
                "text": "\n".join(parts)[:max_chars],
                "links": tweet_links(data["text"], data),
                "errors": errors,
            }
    errors.append(f"syndication: http {status}")
    reader = via_reader(url, max_chars)
    reader["errors"] = errors
    if reader["text"]:
        reader["title"] = reader.get("title") or "Tweet"
        return reader
    return {
        "url": url,
        "final_url": url,
        "method": "twitter-failed",
        "title": "",
        "description": "",
        "text": "",
        "links": [],
        "errors": errors,
    }


def via_reader(url: str, max_chars: int) -> dict:
    status, ctype, final_url, body = run_curl(READER_PREFIX + url, timeout=20)
    text = decode(body, ctype) if status == 200 else ""
    return {
        "url": url,
        "final_url": final_url,
        "method": "reader-proxy",
        "title": "",
        "description": "",
        "text": text[:max_chars],
        "links": links_of(text, url)[:80],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--max-chars", type=int, default=24000)
    ap.add_argument("--no-reader", action="store_true")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    url = args.url.strip()
    if not urlparse(url).scheme:
        url = "https://" + url
    host = (urlparse(url).hostname or "").lower()
    warnings: list[str] = []

    result = fetch_tweet(url, args.max_chars) if host in TWEET_HOSTS else None

    if result is None:
        status, ctype, final_url, body = run_curl(url)
        raw = decode(body, ctype)
        if ctype.startswith("application/pdf") or url.lower().endswith(".pdf"):
            result = {
                "url": url, "final_url": final_url, "method": "pdf",
                "title": meta_of(raw)["title"], "description": "",
                "text": "", "links": [],
            }
            warnings.append("PDF: hand this to the pdf tooling instead of parsing here.")
        else:
            meta = meta_of(raw)
            text = text_from_html(raw)
            result = {
                "url": url,
                "final_url": final_url,
                "method": f"http-{status}",
                "title": meta["title"],
                "description": meta["description"],
                "text": text[: args.max_chars],
                "links": links_of(raw, final_url or url)[:120],
            }
            if status != 200:
                warnings.append(f"HTTP status {status}.")
            if len(text) < MIN_USEFUL_TEXT and not args.no_reader:
                reader = via_reader(url, args.max_chars)
                if len(reader["text"]) > len(text):
                    warnings.append("Page body too thin for direct parsing; used reader proxy instead.")
                    result = reader
                    result["title"] = meta["title"] or result["title"]

    result["warnings"] = warnings + [f"fallback failed: {e}" for e in result.pop("errors", [])]
    result["host"] = host
    result["char_count"] = len(result.get("text") or "")
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
