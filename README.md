# Chidon HaTanach Grader

Automated multilingual grading system for Bible knowledge competitions (Хидон ХаТанах).

## Features

- **Multilingual** — 9+ languages: Russian, German, English, Hebrew, French, Spanish...
- **Question types** — True/False, Multiple Choice, Open-ended with partial credit
- **AI-powered** — open questions evaluated by LLM (Claude, GPT-4o, Gemini)
- **5-stage pipeline** — minimizes API costs by handling simple questions first
- **File converter** — accepts Excel, CSV, PDF, Word, Google Forms exports
- **Reports** — generates Word documents with detailed scoring per participant

## How to Use

1. Select language in the sidebar
2. Enter your AI API key (Anthropic, OpenAI, or Google)
3. Upload Answer Key + Participant Answers (or use File Converter)
4. Click **Run** — results download automatically

## Supported AI Providers

| Provider | Models |
|----------|--------|
| Anthropic (Claude) | Sonnet 4.5, Haiku 3.5 |
| OpenAI | GPT-4o, GPT-4o-mini |
| Google (Gemini) | Gemini 2.0 Flash, Pro |

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```
