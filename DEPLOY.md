# Deploying

Frontend → GitHub Pages (static), backend → a free Hugging Face Docker Space.

```
 GitHub Pages (UI)  ──calls──▶  Hugging Face Space (API)
 ...github.io/mcp-postman-ai-runner   bhamdoesweirdstuff-mcp-postman-ai-runner.hf.space
```

## 1. Backend → Hugging Face Space

```bash
pip install -U huggingface_hub
export HF_TOKEN=hf_xxx        # a WRITE token from https://hf.co/settings/tokens
deploy/deploy_hf.sh bhamdoesweirdstuff mcp-postman-ai-runner
```

Verify: `https://bhamdoesweirdstuff-mcp-postman-ai-runner.hf.space/api/info`.

The Space has **no Ollama**. For LLM analysis on the live demo, add a
`GEMINI_API_KEY` or `ANTHROPIC_API_KEY` secret in the Space settings; otherwise
use the dashboard's deterministic mode (AI analysis off). Full local runs use
Ollama with zero keys.

## 2. Frontend → GitHub Pages

`.github/workflows/deploy-pages.yml` builds with the Space URL baked in and
publishes on every push to `main`. Enable Pages once (Settings → Pages → Source =
GitHub Actions). Pages requires a **public** repo on the free plan.

Site: `https://shubhamsachdeva311205.github.io/mcp-postman-ai-runner/`.
