# Vercel + Hugging Face Legal AI Deployment

This website can be hosted on Vercel from GitHub, but the GGUF model should run on Hugging Face as a dedicated endpoint.

## Why

The model is a large GGUF file and runs through `llama-cpp-python`. A static Vercel site cannot load that model directly in the browser, and Vercel Functions are not the right place to store and run the GGUF model.

The production flow is:

```text
Vercel website -> /api/legal-ai -> Hugging Face llama.cpp endpoint -> GGUF model
```

## What is already wired

- `legal-ai.html` calls `/api/legal-ai` on production.
- `api/legal-ai.js` proxies to the Hugging Face endpoint.
- `api/health.js` checks whether the endpoint is configured.
- `ambuj-legal-llm-starter/` remains as a local fallback and reference implementation.

## Recommended setup

### 1. Create the Hugging Face endpoint

In Hugging Face, create a dedicated Inference Endpoint from this model:

```text
invincibleambuj/Ambuj-Tripathi-Indian-Legal-Llama-GGUF
```

Use the llama.cpp / GGUF-capable endpoint flow, then copy the endpoint URL.

The endpoint URL will look like:

```text
https://<your-endpoint>.endpoints.huggingface.cloud
```

The OpenAI-compatible chat path is:

```text
/v1/chat/completions
```

### 2. Add Vercel environment variables

In Vercel Project Settings -> Environment Variables, add:

```text
LEGAL_AI_HF_ENDPOINT_URL=https://<your-endpoint>.endpoints.huggingface.cloud
LEGAL_AI_HF_TOKEN=your_hugging_face_token
```

If you choose to keep the older Python backend around instead, you can still use:

```text
LEGAL_AI_BACKEND_URL=https://your-backend.example.com
LEGAL_AI_BACKEND_TOKEN=your-secret-token
```

### 3. Deploy website from GitHub

Connect this GitHub repository to Vercel and deploy.

The page:

```text
/legal-ai.html
```

will call:

```text
/api/legal-ai
```

and Vercel will forward the request to Hugging Face.

## Local development

Run the static website:

```bash
python3 -m http.server 4174
```

Run the local model API:

```bash
./ambuj-legal-llm-starter/run-api.sh
```

Open:

```text
http://127.0.0.1:4174/legal-ai.html
```
