#!/usr/bin/env bash
# Push the runner backend to a Hugging Face Docker Space.
#   pip install -U huggingface_hub && huggingface-cli login   # WRITE token
#   deploy/deploy_hf.sh [hf_username] [space_name]
set -euo pipefail

HF_USER="${1:-bhamdoesweirdstuff}"
SPACE="${2:-mcp-postman-ai-runner}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"

huggingface-cli repo create "${SPACE}" --type space --space_sdk docker -y >/dev/null 2>&1 || true
git clone "https://huggingface.co/spaces/${HF_USER}/${SPACE}" "${WORK}"

cp "${REPO_ROOT}/Dockerfile" "${WORK}/Dockerfile"
cp "${REPO_ROOT}/.dockerignore" "${WORK}/.dockerignore"
cp "${REPO_ROOT}/deploy/huggingface/README.md" "${WORK}/README.md"
rm -rf "${WORK}/backend"; cp -R "${REPO_ROOT}/backend" "${WORK}/backend"
find "${WORK}/backend" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "${WORK}/backend/.venv"

cd "${WORK}"
git add -A
git -c user.email="shubhamsachdeva245@gmail.com" -c user.name="Shubham Sachdeva" \
    commit -m "Deploy Postman AI Runner backend" >/dev/null 2>&1 || { echo "Nothing to deploy."; exit 0; }
git push
echo "Space: https://huggingface.co/spaces/${HF_USER}/${SPACE}"
echo "API:   https://${HF_USER}-${SPACE}.hf.space/api/info"
