"""
llm_client.py — Unified LLM interface for Chidon Grader

Supports:
  - Anthropic (Claude)
  - OpenAI (GPT)
  - Google (Gemini)
  - OpenAI-compatible (Llama via Together, Groq, OpenRouter, etc.)

Usage:
  from llm_client import call_llm
  text = call_llm(prompt, provider="anthropic", model="claude-sonnet-4-5-20250929", api_key="sk-...")
"""

import os
import json

# ═══════════════════════════════════════════════════════════════
# PROVIDER REGISTRY
# ═══════════════════════════════════════════════════════════════

PROVIDERS = {
    "anthropic": {
        "label": "Anthropic (Claude)",
        "models": [
            ("claude-sonnet-4-5-20250929", "Claude Sonnet 4.5 — best balance"),
            ("claude-haiku-4-5-20251001", "Claude Haiku 4.5 — fast & cheap"),
            ("claude-opus-4-6", "Claude Opus 4.6 — highest quality"),
        ],
        "key_env": "ANTHROPIC_API_KEY",
        "key_prefix": "sk-ant-",
    },
    "openai": {
        "label": "OpenAI (GPT)",
        "models": [
            ("gpt-4o", "GPT-4o — best balance"),
            ("gpt-4o-mini", "GPT-4o Mini — fast & cheap"),
            ("o3-mini", "o3-mini — reasoning"),
        ],
        "key_env": "OPENAI_API_KEY",
        "key_prefix": "sk-",
    },
    "google": {
        "label": "Google (Gemini)",
        "models": [
            ("gemini-2.0-flash", "Gemini 2.0 Flash — fast"),
            ("gemini-2.5-pro-preview-06-05", "Gemini 2.5 Pro — best quality"),
            ("gemini-2.5-flash-preview-05-20", "Gemini 2.5 Flash — new gen"),
        ],
        "key_env": "GOOGLE_API_KEY",
        "key_prefix": "AI",
    },
    "openai_compat": {
        "label": "OpenAI-Compatible (Llama, etc.)",
        "models": [
            ("meta-llama/Llama-3.3-70B-Instruct-Turbo", "Llama 3.3 70B (Together)"),
            ("llama-3.3-70b-versatile", "Llama 3.3 70B (Groq)"),
            ("meta-llama/llama-4-maverick", "Llama 4 Maverick (Together)"),
        ],
        "key_env": "OPENAI_COMPAT_API_KEY",
        "key_prefix": "",
        "base_urls": {
            "together": "https://api.together.xyz/v1",
            "groq": "https://api.groq.com/openai/v1",
            "openrouter": "https://openrouter.ai/api/v1",
        },
    },
}


# ═══════════════════════════════════════════════════════════════
# API CALLS
# ═══════════════════════════════════════════════════════════════

def call_anthropic(prompt, model, api_key):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def call_openai(prompt, model, api_key):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def call_google(prompt, model, api_key):
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return response.text


def call_openai_compat(prompt, model, api_key, base_url=None):
    from openai import OpenAI

    # Auto-detect base_url from env or default to Together
    if not base_url:
        base_url = os.environ.get("OPENAI_COMPAT_BASE_URL", "https://api.together.xyz/v1")

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


# ═══════════════════════════════════════════════════════════════
# UNIFIED INTERFACE
# ═══════════════════════════════════════════════════════════════

def call_llm(prompt, provider="anthropic", model=None, api_key=None, base_url=None):
    """
    Call any supported LLM provider with a unified interface.

    Args:
        prompt: Text prompt
        provider: "anthropic", "openai", "google", "openai_compat"
        model: Model string (uses default if None)
        api_key: API key (reads from env if None)
        base_url: Base URL for openai_compat provider

    Returns:
        Response text string
    """
    # Defaults
    if not model:
        model = PROVIDERS[provider]["models"][0][0]

    if not api_key:
        env_key = PROVIDERS[provider]["key_env"]
        api_key = os.environ.get(env_key, "")
        if not api_key:
            raise ValueError(f"No API key for {provider}. Set {env_key} or pass api_key.")

    # Route to provider
    if provider == "anthropic":
        return call_anthropic(prompt, model, api_key)
    elif provider == "openai":
        return call_openai(prompt, model, api_key)
    elif provider == "google":
        return call_google(prompt, model, api_key)
    elif provider == "openai_compat":
        return call_openai_compat(prompt, model, api_key, base_url)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_config_from_env():
    """
    Read provider/model/key/base_url from environment variables.
    Used by stage0.py and stage3.py when run as subprocess.
    """
    return {
        "provider": os.environ.get("CHIDON_PROVIDER", "anthropic"),
        "model": os.environ.get("CHIDON_MODEL", "claude-sonnet-4-5-20250929"),
        "api_key": os.environ.get("CHIDON_API_KEY", os.environ.get("ANTHROPIC_API_KEY", "")),
        "base_url": os.environ.get("OPENAI_COMPAT_BASE_URL", ""),
    }
