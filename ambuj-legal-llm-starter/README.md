# Ambuj Legal LLM Starter

A small local starter project for running the Hugging Face GGUF model:

`invincibleambuj/Ambuj-Tripathi-Indian-Legal-Llama-GGUF`

This repo is set up as a separate legal-AI playground so you can test the model without touching the main website.

## What this model is

- GGUF format, 1B parameters, Q4_K_M quantization
- Fine-tuned on Indian legal QA data
- Designed for local inference on CPU or lightweight GPU offload
- Best suited for educational legal Q&A, issue spotting, and drafting assistance

## Important caveat

This is an experimental model. It is not legal advice and should not be relied on for real legal decisions without checking official sources and a qualified advocate.

## How website integration works

The website does not load the GGUF file directly in the browser.

Instead, the flow is:

```text
legal-ai.html -> Vercel /api/legal-ai -> FastAPI backend -> Hugging Face GGUF model
```

This matters because:

- The model file is large and should run server-side.
- Hugging Face tokens must not be exposed in frontend JavaScript.
- `llama-cpp-python` runs in Python, not in a static HTML page.
- Vercel can host the website and proxy requests, while the model backend runs on a Python host such as a Hugging Face Docker Space.

## What this starter does

- Loads the GGUF file with `llama-cpp-python`
- Provides a FastAPI endpoint for the website
- Provides an optional Gradio chat UI for local testing
- Uses a strict Indian-legal system prompt
- Keeps the model path configurable through environment variables

## 1) Download the model

The Hugging Face repo contains the file:

`llama-3.2-1b-instruct.Q4_K_M.gguf`

Recommended download command:

```bash
hf download invincibleambuj/Ambuj-Tripathi-Indian-Legal-Llama-GGUF \
  --include "llama-3.2-1b-instruct.Q4_K_M.gguf" \
  --local-dir ./models
```

That should place the model at:

`./models/llama-3.2-1b-instruct.Q4_K_M.gguf`

If you already have the file from the repo, just copy it into `./models`.

## 2) Install dependencies

```bash
pip install -r requirements.txt
```

If you prefer an isolated environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3) Run the app

For website integration, run the API:

```bash
./run-api.sh
```

Then open the website page:

```text
http://127.0.0.1:4174/legal-ai.html
```

Optional Gradio launcher:

```bash
./run.sh
```

If you prefer manual control:

```bash
export MODEL_PATH=./models/llama-3.2-1b-instruct.Q4_K_M.gguf
python app.py
```

Optional runtime tuning:

- `N_CTX=4096`
- `N_GPU_LAYERS=0` for CPU-only usage
- `N_GPU_LAYERS=20` or similar if your local GPU setup supports it

## Recommended settings

- Temperature: `0.2` to `0.5`
- Top-p: `0.9`
- Max tokens: `768` to `1600`
- Keep prompts short, direct, and legally grounded

## Lawyer workflows supported by the website

The website sends a `workflow` value to the backend so the model can format output as a specific legal work product:

- `legal_notice` - formal legal notice drafts
- `case_brief` - facts, issues, risks, evidence, and next steps
- `clause_review` - clause risks and safer revisions
- `research_memo` - short legal research memo
- `client_email` - polished client-facing email
- `compliance_checklist` - action checklist
- `document_summary` - lawyer-focused summary and missing information
- `general` - open legal analysis

## Alternatives

- LM Studio: load the repo directly and chat with the GGUF file
- llama.cpp: `llama-cli -hf invincibleambuj/Ambuj-Tripathi-Indian-Legal-Llama-GGUF --jinja`

## Good first prompts

- `Summarize the likely issues in a consumer dispute under Indian law and list the documents I should collect.`
- `Draft a short legal notice for a payment default.`
- `Explain IPC Section 302 in simple terms and mention the caveat that exact wording should be verified.`

## Project files

- `app.py` - Gradio chat app
- `server.py` - FastAPI backend used by the website
- `run-api.sh` - one-command API launcher for website integration
- `run.sh` - optional Gradio launcher
- `Dockerfile` - backend container for a Hugging Face Docker Space
- `requirements.txt` - Python dependencies
- `.env.example` - sample local config

## Notes on model quality

The Hugging Face model card describes this as an alpha / proof-of-concept release with known limitations, including possible hallucinations and incorrect section or article references.

That means the app should be used for:

- learning
- drafting support
- brainstorming legal questions

And not for:

- final legal advice
- compliance sign-off
- court filing without verification
