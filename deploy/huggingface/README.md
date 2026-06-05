---
title: Postman AI Runner API
emoji: 🧪
colorFrom: gray
colorTo: green
sdk: docker
app_port: 7860
pinned: false
short_description: Run Postman collections and grade responses with an LLM
---

# Postman AI Runner API

Backend for [mcp-postman-ai-runner](https://github.com/ShubhamSachdeva311205/mcp-postman-ai-runner).
Serves the FastAPI runner; the dashboard UI lives on GitHub Pages.

Health: `GET /api/info`. Docs: `/docs`. This Space has no Ollama — set a
`GEMINI_API_KEY` or `ANTHROPIC_API_KEY` secret for LLM analysis, or use
deterministic mode.
