# Backend image for a Hugging Face Docker Space (or any container host).
# Serves the FastAPI runner on port 7860 (HF Spaces default).
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend

ENV PORT=7860
EXPOSE 7860

# allow the GitHub Pages frontend to call this API (override at deploy time)
ENV MCP_ALLOWED_ORIGINS="https://shubhamsachdeva311205.github.io"
# the hosted Space has no Ollama; set GEMINI_API_KEY/ANTHROPIC_API_KEY as Space
# secrets to enable LLM analysis, otherwise use deterministic mode in the UI.

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
