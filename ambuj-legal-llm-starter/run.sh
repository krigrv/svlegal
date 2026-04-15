#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
MODEL_REPO="invincibleambuj/Ambuj-Tripathi-Indian-Legal-Llama-GGUF"
MODEL_NAME="llama-3.2-1b-instruct.Q4_K_M.gguf"
MODEL_DIR="${ROOT_DIR}/models"
MODEL_PATH="${MODEL_PATH:-${MODEL_DIR}/${MODEL_NAME}}"

cd "${SCRIPT_DIR}"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

mkdir -p "${MODEL_DIR}"

if [ ! -f "${MODEL_PATH}" ]; then
  if command -v hf >/dev/null 2>&1; then
    hf download "${MODEL_REPO}" \
      --include "${MODEL_NAME}" \
      --local-dir "${MODEL_DIR}"
  else
    cat <<EOF
Model file not found at:
${MODEL_PATH}

Install the Hugging Face CLI as `hf`, or download the file manually and place it in:
${MODEL_DIR}
EOF
    exit 1
  fi
fi

export MODEL_PATH
export PORT="${PORT:-7860}"

exec python app.py
