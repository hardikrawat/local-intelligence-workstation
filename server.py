#!/usr/bin/env python3
"""
Ollama Studio Web Server & Reverse Proxy
Serves static UI files and proxies /api/* requests to local Ollama daemon (127.0.0.1:11434).
Allows secure remote access via ngrok/tunnels without CORS or Mixed Content errors.

Model Hub Backend:
  /hub/ollama/search   – Scrapes ollama.com/search for model listings
  /hub/ollama/tags     – Fetches available tags for a specific ollama model
  /hub/hf/search       – Searches HuggingFace Hub API for GGUF models
  /hub/hf/model        – Fetches detailed model info from HuggingFace
"""

import sys
import os
import json
import urllib.request
import urllib.error
import urllib.parse
import re
import html
import ssl
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

OLLAMA_BACKEND = "http://127.0.0.1:11434"
DEFAULT_PORT = 3300

# Cache with TTL
_cache = {}
_cache_lock = threading.Lock()
CACHE_TTL = 300  # 5 minutes


def cache_get(key):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.time() - entry["ts"]) < CACHE_TTL:
            return entry["data"]
    return None


def cache_set(key, data):
    with _cache_lock:
        _cache[key] = {"data": data, "ts": time.time()}


def make_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


SSL_CTX = make_ssl_context()

# ─── Ollama Registry Scraper ─────────────────────────────────────────────────

OLLAMA_LIBRARY_URL = "https://ollama.com/search"
OLLAMA_LIBRARY_API = "https://ollama.com/api/models"

# Model type classification database
MODEL_TYPE_KEYWORDS = {
    "vision": ["vision", "llava", "moondream", "bakllava", "minicpm-v", "cogvlm",
               "internvl", "monkey", "yi-vl", "qwen-vl", "qwen2-vl", "pixtral",
               "gemma3", "llama3.2-vision"],
    "code": ["coder", "codellama", "starcoder", "deepseek-coder", "codestral",
             "codegemma", "codeqwen", "granite-code", "stable-code", "yi-coder",
             "qwen2.5-coder"],
    "embedding": ["embed", "nomic-embed", "mxbai-embed", "snowflake-arctic-embed",
                  "all-minilm", "bge-", "gte-"],
    "audio": ["whisper", "audio", "speech", "voice", "tts"],
    "video": ["video", "cogvideo"],
    "math": ["math", "mathstral", "qwen2-math", "deepseek-math", "internlm2-math"],
    "reasoning": ["r1", "qwq", "reason", "deepseek-r1", "qwen3"],
    "tool_use": ["firefunction", "hermes", "nexusraven", "gorilla"],
    "medical": ["medllama", "meditron", "med-", "clinical", "medical", "biomistral"],
    "legal": ["saul", "legal", "law"],
    "finance": ["finance", "fin-"],
    "creative": ["neural-chat", "starling", "openhermes", "dolphin", "nous-hermes"],
}


def classify_model_types(name, description=""):
    """Classify a model into capability categories based on name and description."""
    text = f"{name} {description}".lower()
    types = set()
    for category, keywords in MODEL_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                types.add(category)
                break
    if not types:
        types.add("text")
    return sorted(types)


def fetch_ollama_models(query="", category=""):
    """Fetch models from the Ollama library API."""
    cache_key = f"ollama:{query}:{category}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    try:
        # Use the Ollama website search API
        params = {}
        if query:
            params["q"] = query
        if category:
            params["c"] = category

        url = OLLAMA_LIBRARY_URL
        if params:
            url += "?" + urllib.parse.urlencode(params)

        req = urllib.request.Request(url, headers={
            "User-Agent": "OllamaStudio/1.0",
            "Accept": "text/html,application/xhtml+xml"
        })

        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
            body = resp.read().decode("utf-8", errors="replace")

        models = parse_ollama_search_html(body)

        # Also try the JSON API endpoint for richer data
        try:
            api_url = "https://ollama.com/api/models"
            if query:
                api_url += "?" + urllib.parse.urlencode({"q": query})

            api_req = urllib.request.Request(api_url, headers={
                "User-Agent": "OllamaStudio/1.0",
                "Accept": "application/json"
            })

            with urllib.request.urlopen(api_req, timeout=15, context=SSL_CTX) as resp:
                api_data = json.loads(resp.read().decode("utf-8"))

            if isinstance(api_data, dict) and "models" in api_data:
                api_models = api_data["models"]
                # Merge API data with scraped data
                api_map = {}
                for m in api_models:
                    name = m.get("name", "")
                    api_map[name] = m

                # Enrich scraped models with API data
                enriched = []
                seen_names = set()
                for m in models:
                    name = m.get("name", "")
                    if name in api_map:
                        api_m = api_map[name]
                        m["pulls"] = api_m.get("pull_count", m.get("pulls", ""))
                        m["tags_count"] = api_m.get("tags_count", 0)
                        m["updated"] = api_m.get("updated_at", m.get("updated", ""))
                        m["description"] = api_m.get("description", m.get("description", ""))
                        m["capabilities"] = api_m.get("capabilities", [])
                    enriched.append(m)
                    seen_names.add(name)

                # Add API-only models not in scraped results
                for name, api_m in api_map.items():
                    if name not in seen_names:
                        enriched.append({
                            "name": name,
                            "description": api_m.get("description", ""),
                            "pulls": api_m.get("pull_count", ""),
                            "tags_count": api_m.get("tags_count", 0),
                            "updated": api_m.get("updated_at", ""),
                            "sizes": [],
                            "capabilities": api_m.get("capabilities", []),
                            "types": classify_model_types(name, api_m.get("description", "")),
                            "source": "ollama"
                        })

                models = enriched if enriched else models

        except Exception:
            pass  # API endpoint may not be available, fall back to scraped data

        result = {"models": models, "source": "ollama.com", "query": query}
        cache_set(cache_key, result)
        return result

    except Exception as e:
        return {"models": [], "error": str(e), "source": "ollama.com", "query": query}


def parse_ollama_search_html(body):
    """Parse Ollama search page HTML to extract model listings."""
    models = []

    # Parse model cards from search results HTML
    # Match <li> or <a> blocks that contain model info
    # Pattern adapted for ollama.com/search page structure

    # Try matching anchor tags with model info
    # The search page uses cards with href="/library/{model}"
    card_pattern = re.compile(
        r'<a[^>]*href="[/]library/([^"]+)"[^>]*>(.*?)</a>',
        re.DOTALL | re.IGNORECASE
    )

    # Also try matching model names and descriptions from structured elements
    name_pattern = re.compile(
        r'(?:<h[23][^>]*>|<span[^>]*class="[^"]*truncate[^"]*"[^>]*>)\s*([\w./-]+(?::[\w.]+)?)\s*(?:</h[23]>|</span>)',
        re.IGNORECASE
    )

    desc_pattern = re.compile(
        r'<p[^>]*class="[^"]*(?:description|text-neutral)[^"]*"[^>]*>(.*?)</p>',
        re.DOTALL | re.IGNORECASE
    )

    pulls_pattern = re.compile(
        r'(\d+(?:\.\d+)?[KkMmBb]?)\s*(?:Pulls?|Downloads?|pulls)',
        re.IGNORECASE
    )

    # Extract model blocks
    # Look for structured model card sections
    block_pattern = re.compile(
        r'<(?:li|div|a)[^>]*(?:class="[^"]*(?:model|card|item)[^"]*"|href="/library/)[^>]*>(.*?)</(?:li|div|a)>',
        re.DOTALL | re.IGNORECASE
    )

    blocks = block_pattern.findall(body)

    # If no structured blocks found, try extracting from full page
    if not blocks:
        blocks = [body]

    seen = set()
    for block in blocks:
        # Extract model name from href or heading
        name_match = re.search(r'href="[/]library/([^"/]+)"', block, re.IGNORECASE)
        if not name_match:
            name_match = re.search(r'<h\d[^>]*>\s*([\w.-]+(?:/[\w.-]+)?)\s*</h\d>', block, re.IGNORECASE)

        if name_match:
            name = name_match.group(1).strip()
            if name in seen or len(name) < 2:
                continue
            seen.add(name)

            # Extract description
            desc = ""
            desc_match = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
            if desc_match:
                desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()

            # Extract pull count
            pulls = ""
            pulls_match = pulls_pattern.search(block)
            if pulls_match:
                pulls = pulls_match.group(1)

            # Extract sizes/tags
            sizes = []
            size_matches = re.findall(r'(\d+(?:\.\d+)?[bBmM])\b', block)
            sizes = list(set(size_matches))

            # Extract updated time
            updated = ""
            updated_match = re.search(r'Updated?\s+([\w\s,]+ago|[\d-]+)', block, re.IGNORECASE)
            if updated_match:
                updated = updated_match.group(1).strip()

            models.append({
                "name": name,
                "description": html.unescape(desc) if desc else "",
                "pulls": pulls,
                "sizes": sizes,
                "updated": updated,
                "types": classify_model_types(name, desc),
                "source": "ollama"
            })

    # If scraping yielded nothing, provide popular fallback models
    if not models:
        models = get_popular_ollama_models()

    return models


def get_popular_ollama_models():
    """Return a curated list of popular Ollama models as fallback."""
    return [
        {"name": "llama3.3", "description": "Meta's Llama 3.3 is a powerful 70B model with multilingual support", "pulls": "50M+", "sizes": ["70b"], "updated": "", "types": ["text", "reasoning"], "source": "ollama"},
        {"name": "llama3.2", "description": "Meta's Llama 3.2 — Available in 1B, 3B for text and 11B, 90B with vision", "pulls": "30M+", "sizes": ["1b", "3b", "11b", "90b"], "updated": "", "types": ["text", "vision"], "source": "ollama"},
        {"name": "llama3.2-vision", "description": "Llama 3.2-Vision models for image understanding and visual reasoning", "pulls": "10M+", "sizes": ["11b", "90b"], "updated": "", "types": ["vision"], "source": "ollama"},
        {"name": "deepseek-r1", "description": "DeepSeek R1 — State-of-art reasoning model with chain-of-thought", "pulls": "40M+", "sizes": ["1.5b", "7b", "8b", "14b", "32b", "70b", "671b"], "updated": "", "types": ["text", "reasoning"], "source": "ollama"},
        {"name": "qwen3", "description": "Alibaba's Qwen 3 — hybrid thinking model with superior reasoning", "pulls": "15M+", "sizes": ["0.6b", "1.7b", "4b", "8b", "14b", "30b", "32b", "235b"], "updated": "", "types": ["text", "reasoning"], "source": "ollama"},
        {"name": "qwen2.5-coder", "description": "Qwen 2.5 Coder — Specialized coding model with FIM support", "pulls": "10M+", "sizes": ["0.5b", "1.5b", "3b", "7b", "14b", "32b"], "updated": "", "types": ["code"], "source": "ollama"},
        {"name": "gemma3", "description": "Google's Gemma 3 — Compact and powerful with multimodal vision support", "pulls": "12M+", "sizes": ["1b", "4b", "12b", "27b"], "updated": "", "types": ["text", "vision"], "source": "ollama"},
        {"name": "phi4", "description": "Microsoft Phi-4 — Small, fast reasoning model", "pulls": "8M+", "sizes": ["14b"], "updated": "", "types": ["text", "reasoning"], "source": "ollama"},
        {"name": "mistral", "description": "Mistral 7B — Fast, efficient general-purpose model from Mistral AI", "pulls": "25M+", "sizes": ["7b"], "updated": "", "types": ["text"], "source": "ollama"},
        {"name": "mixtral", "description": "Mistral's Mixture of Experts model — 8x7B and 8x22B variants", "pulls": "8M+", "sizes": ["8x7b", "8x22b"], "updated": "", "types": ["text"], "source": "ollama"},
        {"name": "codestral", "description": "Mistral's Codestral — Purpose-built code generation model", "pulls": "3M+", "sizes": ["22b"], "updated": "", "types": ["code"], "source": "ollama"},
        {"name": "command-r", "description": "Cohere Command R — Optimized for RAG and tool use", "pulls": "5M+", "sizes": ["35b", "104b"], "updated": "", "types": ["text", "tool_use"], "source": "ollama"},
        {"name": "llava", "description": "LLaVA — Large Language and Vision Assistant for image understanding", "pulls": "15M+", "sizes": ["7b", "13b", "34b"], "updated": "", "types": ["vision"], "source": "ollama"},
        {"name": "nomic-embed-text", "description": "Nomic AI text embeddings — High-performance 768-dim embedding model", "pulls": "12M+", "sizes": ["137m"], "updated": "", "types": ["embedding"], "source": "ollama"},
        {"name": "mxbai-embed-large", "description": "MixedBread AI — State-of-art embedding model for retrieval", "pulls": "5M+", "sizes": ["335m"], "updated": "", "types": ["embedding"], "source": "ollama"},
        {"name": "starcoder2", "description": "BigCode StarCoder 2 — Trained on The Stack v2 for code generation", "pulls": "4M+", "sizes": ["3b", "7b", "15b"], "updated": "", "types": ["code"], "source": "ollama"},
        {"name": "moondream", "description": "Moondream — Tiny but capable vision-language model", "pulls": "3M+", "sizes": ["1.8b"], "updated": "", "types": ["vision"], "source": "ollama"},
        {"name": "dolphin-mixtral", "description": "Dolphin Mixtral — Uncensored mixture-of-experts model", "pulls": "5M+", "sizes": ["8x7b", "8x22b"], "updated": "", "types": ["text", "creative"], "source": "ollama"},
        {"name": "yi", "description": "01.AI Yi — Strong bilingual (English/Chinese) foundation model", "pulls": "4M+", "sizes": ["6b", "9b", "34b"], "updated": "", "types": ["text"], "source": "ollama"},
        {"name": "neural-chat", "description": "Intel Neural Chat — Fine-tuned for helpful assistant responses", "pulls": "3M+", "sizes": ["7b"], "updated": "", "types": ["text", "creative"], "source": "ollama"},
        {"name": "stable-code", "description": "Stability AI — Coding completion model based on Stable LM", "pulls": "2M+", "sizes": ["3b"], "updated": "", "types": ["code"], "source": "ollama"},
        {"name": "solar", "description": "Upstage Solar — Compact high-performance model", "pulls": "3M+", "sizes": ["10.7b"], "updated": "", "types": ["text"], "source": "ollama"},
        {"name": "mathstral", "description": "Mistral MathStral — Specialized mathematics and STEM model", "pulls": "1M+", "sizes": ["7b"], "updated": "", "types": ["math"], "source": "ollama"},
        {"name": "meditron", "description": "EPFL Meditron — Specialized medical/clinical knowledge model", "pulls": "500K+", "sizes": ["7b", "70b"], "updated": "", "types": ["medical"], "source": "ollama"},
    ]


def fetch_ollama_model_tags(model_name):
    """Fetch available tags for a specific Ollama model."""
    cache_key = f"ollama_tags:{model_name}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    try:
        url = f"https://ollama.com/library/{urllib.parse.quote(model_name, safe='')}/tags"
        req = urllib.request.Request(url, headers={
            "User-Agent": "OllamaStudio/1.0",
            "Accept": "text/html,application/xhtml+xml"
        })

        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
            body = resp.read().decode("utf-8", errors="replace")

        tags = parse_ollama_tags_html(body, model_name)

        # Also try the API endpoint
        try:
            api_url = f"https://ollama.com/api/models/{urllib.parse.quote(model_name, safe='')}"
            api_req = urllib.request.Request(api_url, headers={
                "User-Agent": "OllamaStudio/1.0",
                "Accept": "application/json"
            })
            with urllib.request.urlopen(api_req, timeout=10, context=SSL_CTX) as resp:
                api_data = json.loads(resp.read().decode("utf-8"))

            if isinstance(api_data, dict):
                api_tags = api_data.get("tags", [])
                if api_tags and isinstance(api_tags, list):
                    # Merge with scraped tags
                    existing_names = {t["tag"] for t in tags}
                    for t in api_tags:
                        tag_name = t if isinstance(t, str) else t.get("name", "")
                        if tag_name and tag_name not in existing_names:
                            size = ""
                            if isinstance(t, dict):
                                size_bytes = t.get("size", 0)
                                if size_bytes:
                                    size = format_bytes_py(size_bytes)
                            tags.append({
                                "tag": tag_name,
                                "full_name": f"{model_name}:{tag_name}",
                                "size": size,
                                "quantization": extract_quant(tag_name),
                                "parameters": extract_params(tag_name)
                            })
        except Exception:
            pass

        result = {"model": model_name, "tags": tags}
        cache_set(cache_key, result)
        return result

    except Exception as e:
        return {"model": model_name, "tags": [], "error": str(e)}


def parse_ollama_tags_html(body, model_name):
    """Parse tags page HTML."""
    tags = []
    seen = set()

    # Look for tag names in the HTML — they typically appear as links or text
    tag_patterns = [
        re.compile(r'href="[/]library/' + re.escape(model_name) + r':([^"]+)"', re.IGNORECASE),
        re.compile(r'>\s*' + re.escape(model_name) + r':(\S+)\s*<', re.IGNORECASE),
        re.compile(r'"tag"\s*:\s*"([^"]+)"', re.IGNORECASE),
    ]

    for pattern in tag_patterns:
        for match in pattern.finditer(body):
            tag = match.group(1).strip()
            if tag and tag not in seen and len(tag) < 100:
                seen.add(tag)

                # Try to extract size info near this tag
                pos = match.start()
                context = body[max(0, pos - 200):min(len(body), pos + 500)]
                size = ""
                size_match = re.search(r'(\d+(?:\.\d+)?\s*(?:GB|MB|KB|TB))', context, re.IGNORECASE)
                if size_match:
                    size = size_match.group(1)

                tags.append({
                    "tag": tag,
                    "full_name": f"{model_name}:{tag}",
                    "size": size,
                    "quantization": extract_quant(tag),
                    "parameters": extract_params(tag)
                })

    # If no tags found, provide common defaults
    if not tags:
        for default_tag in ["latest", "7b", "8b", "14b", "70b"]:
            tags.append({
                "tag": default_tag,
                "full_name": f"{model_name}:{default_tag}",
                "size": "",
                "quantization": extract_quant(default_tag),
                "parameters": extract_params(default_tag)
            })

    return tags


def extract_quant(tag_str):
    """Extract quantization level from a tag string."""
    tag = tag_str.lower()
    quant_patterns = ["q2_k", "q3_k_s", "q3_k_m", "q3_k_l", "q4_0", "q4_1",
                      "q4_k_s", "q4_k_m", "q5_0", "q5_1", "q5_k_s", "q5_k_m",
                      "q6_k", "q8_0", "fp16", "fp32", "bf16", "f16", "f32",
                      "iq2_xxs", "iq2_xs", "iq3_xxs", "iq3_s", "iq4_nl", "iq4_xs"]
    for q in quant_patterns:
        if q in tag:
            return q.upper()
    return ""


def extract_params(tag_str):
    """Extract parameter size from a tag string."""
    match = re.search(r'(\d+(?:\.\d+)?)\s*[bB]\b', tag_str)
    if match:
        return match.group(0).upper()
    return ""


def format_bytes_py(size_bytes):
    """Format bytes into human-readable string."""
    if not size_bytes:
        return ""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


# ─── HuggingFace Hub API ─────────────────────────────────────────────────────

DEFAULT_HF_ENDPOINT = "https://huggingface.co"


def normalize_endpoint(endpoint=None):
    """Normalize and ensure scheme on Hugging Face API endpoint/mirror."""
    ep = (endpoint or DEFAULT_HF_ENDPOINT).strip().rstrip("/")
    if not ep:
        return DEFAULT_HF_ENDPOINT
    if not ep.startswith("http://") and not ep.startswith("https://"):
        ep = "https://" + ep
    return ep


def fetch_hf_models(query="", model_type="", sort="downloads", limit=40,
                    token=None, endpoint=None, gguf_only=True):
    """Search HuggingFace Hub with full configuration support (token, mirror, filters)."""
    base_endpoint = normalize_endpoint(endpoint)
    clean_token = (token or "").strip()
    cache_key = f"hf:{base_endpoint}:{query}:{model_type}:{sort}:{limit}:{gguf_only}:{'auth' if clean_token else 'anon'}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    try:
        # HuggingFace sort field mapping
        sort_map = {
            "downloads": "downloads",
            "likes": "likes",
            "trending": "trendingScore",
            "trendingScore": "trendingScore",
            "newest": "lastModified",
            "lastModified": "lastModified",
            "created": "createdAt",
        }
        hf_sort = sort_map.get(sort, "downloads")

        params = {
            "limit": str(min(max(1, limit), 100)),
            "sort": hf_sort,
            "direction": "-1",
            "full": "true",
        }

        # Build search query
        search_terms = []
        if query:
            search_terms.append(query)
        if gguf_only:
            search_terms.append("gguf")

        if search_terms:
            params["search"] = " ".join(search_terms)

        # Filter by pipeline task if specified
        task_map = {
            "text": "text-generation",
            "reasoning": "text-generation",
            "vision": "image-text-to-text",
            "audio": "automatic-speech-recognition",
            "image": "image-to-text",
            "embedding": "feature-extraction",
            "code": "text-generation",
            "translation": "translation",
            "summarization": "summarization",
            "question-answering": "question-answering",
            "tts": "text-to-speech",
            "image-generation": "text-to-image",
            "video": "text-to-video",
        }
        if model_type and model_type in task_map:
            params["pipeline_tag"] = task_map[model_type]

        url = f"{base_endpoint}/api/models?{urllib.parse.urlencode(params)}"
        headers = {
            "User-Agent": "OllamaStudio/1.0",
            "Accept": "application/json"
        }
        if clean_token:
            headers["Authorization"] = f"Bearer {clean_token}"

        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        models = []
        for m in data:
            model_id = m.get("modelId", m.get("id", ""))
            if not model_id:
                continue

            tags = m.get("tags", [])
            has_gguf = "gguf" in tags or any("gguf" in t.lower() for t in tags)

            # If user requested gguf_only, verify the model has gguf tag or gguf files
            siblings = m.get("siblings", [])
            gguf_files = [s for s in siblings if s.get("rfilename", "").lower().endswith(".gguf")]
            if gguf_only and not (has_gguf or gguf_files or "gguf" in model_id.lower()):
                continue

            pipeline_tag = m.get("pipeline_tag", "")
            model_types = classify_hf_model_type(model_id, pipeline_tag, tags)

            # Extract file sizes & quantizations
            file_info = []
            for f in gguf_files[:15]:
                fname = f.get("rfilename", "")
                fsize = f.get("size", 0)
                file_info.append({
                    "name": fname,
                    "size": format_bytes_py(fsize) if fsize else "",
                    "size_bytes": fsize,
                    "quantization": extract_quant(fname),
                    "parameters": extract_params(fname)
                })

            models.append({
                "id": model_id,
                "name": model_id.split("/")[-1] if "/" in model_id else model_id,
                "author": model_id.split("/")[0] if "/" in model_id else "",
                "description": m.get("description", ""),
                "downloads": m.get("downloads", 0),
                "likes": m.get("likes", 0),
                "pipeline_tag": pipeline_tag,
                "tags": tags[:20],
                "types": model_types,
                "has_gguf": has_gguf or bool(gguf_files),
                "gguf_files": file_info,
                "last_modified": m.get("lastModified", ""),
                "private": m.get("private", False),
                "library_name": m.get("library_name", ""),
                "source": "huggingface",
                "url": f"{base_endpoint}/{model_id}"
            })

        result = {
            "models": models,
            "source": "huggingface",
            "endpoint": base_endpoint,
            "query": query,
            "total": len(models),
            "authenticated": bool(clean_token)
        }
        cache_set(cache_key, result)
        return result

    except urllib.error.HTTPError as e:
        err_msg = f"HuggingFace API HTTP {e.code}"
        if e.code == 401:
            err_msg = "Invalid or expired Hugging Face token. Check your token in HF Settings."
        elif e.code == 403:
            err_msg = "Access forbidden. A Hugging Face token may be required for this repository."
        elif e.code == 429:
            err_msg = "Rate limit reached. Add a Hugging Face API token in HF Settings for higher limits."
        return {"models": [], "error": err_msg, "source": "huggingface", "code": e.code}
    except Exception as e:
        return {"models": [], "error": str(e), "source": "huggingface", "query": query}


def fetch_hf_model_detail(model_id, token=None, endpoint=None):
    """Fetch detailed info for a specific HuggingFace model."""
    base_endpoint = normalize_endpoint(endpoint)
    clean_token = (token or "").strip()
    cache_key = f"hf_detail:{base_endpoint}:{model_id}:{'auth' if clean_token else 'anon'}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    try:
        url = f"{base_endpoint}/api/models/{urllib.parse.quote(model_id, safe='/')}"
        headers = {
            "User-Agent": "OllamaStudio/1.0",
            "Accept": "application/json"
        }
        if clean_token:
            headers["Authorization"] = f"Bearer {clean_token}"

        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        siblings = data.get("siblings", [])
        gguf_files = []
        for s in siblings:
            fname = s.get("rfilename", "")
            if fname.lower().endswith(".gguf"):
                fsize = s.get("size", 0)
                gguf_files.append({
                    "name": fname,
                    "size": format_bytes_py(fsize),
                    "size_bytes": fsize,
                    "quantization": extract_quant(fname),
                    "parameters": extract_params(fname)
                })

        result = {
            "id": data.get("modelId", model_id),
            "author": data.get("author", model_id.split("/")[0] if "/" in model_id else ""),
            "description": data.get("description", ""),
            "downloads": data.get("downloads", 0),
            "likes": data.get("likes", 0),
            "pipeline_tag": data.get("pipeline_tag", ""),
            "tags": data.get("tags", []),
            "gguf_files": gguf_files,
            "card_data": data.get("cardData", {}),
            "last_modified": data.get("lastModified", ""),
            "library_name": data.get("library_name", ""),
            "url": f"{base_endpoint}/{model_id}",
            "source": "huggingface",
            "endpoint": base_endpoint,
            "private": data.get("private", False)
        }

        cache_set(cache_key, result)
        return result

    except urllib.error.HTTPError as e:
        err_msg = f"HTTP {e.code}"
        if e.code == 401:
            err_msg = "Unauthorized. Please set a valid Hugging Face token."
        elif e.code == 404:
            err_msg = "Model not found on Hugging Face."
        return {"error": err_msg, "id": model_id, "code": e.code}
    except Exception as e:
        return {"error": str(e), "id": model_id}


def verify_hf_token(token, endpoint=None):
    """Verify Hugging Face API token using /api/whoami-v2."""
    base_endpoint = normalize_endpoint(endpoint)
    clean_token = (token or "").strip()
    if not clean_token:
        return {"valid": False, "error": "No token provided"}

    try:
        url = f"{base_endpoint}/api/whoami-v2"
        headers = {
            "User-Agent": "OllamaStudio/1.0",
            "Authorization": f"Bearer {clean_token}",
            "Accept": "application/json"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        return {
            "valid": True,
            "username": data.get("name", ""),
            "fullname": data.get("fullname", ""),
            "email": data.get("email", ""),
            "avatar": data.get("avatarUrl", ""),
            "plan": data.get("plan", "free"),
            "orgs": [o.get("name") for o in data.get("orgs", []) if isinstance(o, dict)],
            "auth_type": data.get("auth", {}).get("type", "api_token"),
            "endpoint": base_endpoint
        }
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {"valid": False, "error": "Invalid or expired Hugging Face token"}
        return {"valid": False, "error": f"Hugging Face returned HTTP {e.code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def ping_hf_endpoint(endpoint=None):
    """Test connectivity and measure latency to Hugging Face or mirror."""
    base_endpoint = normalize_endpoint(endpoint)
    start = time.time()
    try:
        url = f"{base_endpoint}/api/models?limit=1"
        req = urllib.request.Request(url, headers={
            "User-Agent": "OllamaStudio/1.0",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as resp:
            elapsed_ms = round((time.time() - start) * 1000)
            return {
                "online": resp.status == 200,
                "status": resp.status,
                "latency_ms": elapsed_ms,
                "endpoint": base_endpoint
            }
    except Exception as e:
        elapsed_ms = round((time.time() - start) * 1000)
        return {
            "online": False,
            "error": str(e),
            "latency_ms": elapsed_ms,
            "endpoint": base_endpoint
        }


def classify_hf_model_type(model_id, pipeline_tag, tags):
    """Classify HuggingFace model types from pipeline tag and tags."""
    types = set()

    pipeline_map = {
        "text-generation": "text",
        "text2text-generation": "text",
        "image-text-to-text": "vision",
        "visual-question-answering": "vision",
        "image-to-text": "vision",
        "automatic-speech-recognition": "audio",
        "audio-classification": "audio",
        "text-to-speech": "audio",
        "text-to-audio": "audio",
        "text-to-image": "image",
        "image-to-image": "image",
        "feature-extraction": "embedding",
        "sentence-similarity": "embedding",
        "fill-mask": "text",
        "translation": "text",
        "summarization": "text",
        "question-answering": "text",
        "conversational": "text",
        "text-to-video": "video",
        "video-classification": "video",
    }

    if pipeline_tag in pipeline_map:
        types.add(pipeline_map[pipeline_tag])

    # Check tags
    tag_set = set(t.lower() for t in tags)
    if "code" in tag_set or any("code" in t for t in tag_set):
        types.add("code")
    if "math" in tag_set:
        types.add("math")
    if "vision" in tag_set or "multimodal" in tag_set:
        types.add("vision")

    # Check model name
    name_types = classify_model_types(model_id)
    types.update(name_types)

    if not types:
        types.add("text")

    return sorted(types)


# ─── HTTP Request Handler ────────────────────────────────────────────────────

class OllamaProxyHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for all responses
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE, PUT")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        elif self.path.startswith("/api/"):
            self.proxy_request("GET")
        elif self.path.startswith("/hub/"):
            self.handle_hub_request()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.proxy_request("POST")
        elif self.path.startswith("/hub/"):
            self.handle_hub_request()
        else:
            self.send_error(404, "Not Found")

    def do_DELETE(self):
        if self.path.startswith("/api/"):
            self.proxy_request("DELETE")
        else:
            self.send_error(404, "Not Found")

    def handle_hub_request(self):
        """Route Model Hub API requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = dict(urllib.parse.parse_qsl(parsed.query))

        # Also read POST body if present
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
            try:
                post_params = json.loads(body)
                params.update(post_params)
            except Exception:
                pass

        # Extract HF configuration from headers or params
        hf_token = params.get("token", params.get("hf_token", ""))
        if not hf_token:
            auth_header = self.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                hf_token = auth_header[7:].strip()
        hf_endpoint = params.get("endpoint", params.get("hf_endpoint", "")).strip()

        try:
            if path == "/hub/ollama/search":
                result = fetch_ollama_models(
                    query=params.get("q", params.get("query", "")),
                    category=params.get("c", params.get("category", ""))
                )
            elif path == "/hub/ollama/tags":
                model = params.get("model", params.get("name", ""))
                if not model:
                    result = {"error": "Missing 'model' parameter"}
                else:
                    result = fetch_ollama_model_tags(model)
            elif path == "/hub/ollama/popular":
                result = {"models": get_popular_ollama_models(), "source": "ollama.com"}
            elif path == "/hub/hf/search":
                gguf_only_val = params.get("gguf_only", "true")
                is_gguf_only = gguf_only_val in [True, "true", "1", "yes"]
                result = fetch_hf_models(
                    query=params.get("q", params.get("query", "")),
                    model_type=params.get("type", params.get("task", "")),
                    sort=params.get("sort", "downloads"),
                    limit=int(params.get("limit", 40)),
                    token=hf_token,
                    endpoint=hf_endpoint,
                    gguf_only=is_gguf_only
                )
            elif path == "/hub/hf/model":
                model_id = params.get("id", params.get("model", ""))
                if not model_id:
                    result = {"error": "Missing 'id' parameter"}
                else:
                    result = fetch_hf_model_detail(model_id, token=hf_token, endpoint=hf_endpoint)
            elif path == "/hub/hf/whoami":
                result = verify_hf_token(hf_token, endpoint=hf_endpoint)
            elif path == "/hub/hf/ping":
                result = ping_hf_endpoint(endpoint=hf_endpoint)
            elif path == "/hub/categories":
                result = {
                    "categories": [
                        {"id": "text", "label": "Text / Chat", "icon": "💬", "desc": "General-purpose language models for conversation and text generation"},
                        {"id": "reasoning", "label": "Reasoning", "icon": "🧠", "desc": "Chain-of-thought and advanced reasoning models"},
                        {"id": "code", "label": "Code", "icon": "💻", "desc": "Programming and code generation models"},
                        {"id": "vision", "label": "Vision", "icon": "👁️", "desc": "Multimodal models that understand images"},
                        {"id": "embedding", "label": "Embedding", "icon": "🔗", "desc": "Text embedding models for search and retrieval"},
                        {"id": "math", "label": "Math", "icon": "📐", "desc": "Mathematics and STEM-focused models"},
                        {"id": "audio", "label": "Audio", "icon": "🎵", "desc": "Speech recognition, TTS, and audio processing models"},
                        {"id": "video", "label": "Video", "icon": "🎬", "desc": "Video understanding and generation models"},
                        {"id": "tool_use", "label": "Tool Use", "icon": "🔧", "desc": "Models optimized for function calling and tool use"},
                        {"id": "medical", "label": "Medical", "icon": "🏥", "desc": "Healthcare and clinical knowledge models"},
                        {"id": "creative", "label": "Creative", "icon": "✨", "desc": "Creative writing and uncensored models"},
                    ]
                }
            else:
                result = {"error": f"Unknown hub endpoint: {path}"}

            self.send_json_response(result)

        except Exception as e:
            self.send_json_response({"error": str(e)}, status=500)

    def send_json_response(self, data, status=200):
        """Send a JSON response."""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def proxy_request(self, method):
        target_url = f"{OLLAMA_BACKEND}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req = urllib.request.Request(target_url, data=body, method=method)
        for h, v in self.headers.items():
            if h.lower() not in ["host", "content-length"]:
                req.add_header(h, v)

        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                self.send_response(resp.status)
                for h, v in resp.getheaders():
                    if h.lower() not in ["transfer-encoding", "content-length"]:
                        self.send_header(h, v)
                self.end_headers()

                # Stream response chunks immediately
                while True:
                    chunk = resp.read(1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err_data = json.dumps({"error": f"Ollama proxy error: {str(e)}"}).encode()
            self.wfile.write(err_data)

    def log_message(self, format, *args):
        """Suppress default logging for cleaner output, except errors."""
        if args and isinstance(args[0], str) and ("404" in args[0] or "500" in args[0] or "502" in args[0]):
            super().log_message(format, *args)


def run():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    HTTPServer.allow_reuse_address = True
    server = HTTPServer(("0.0.0.0", port), OllamaProxyHandler)
    print(f"Ollama Studio server & proxy running on http://0.0.0.0:{port}")
    print(f"Forwarding /api/* -> {OLLAMA_BACKEND} (CORS & HTTPS-tunnel safe)")
    print(f"Model Hub API endpoints: /hub/ollama/search, /hub/hf/search, /hub/categories")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()

if __name__ == "__main__":
    run()
