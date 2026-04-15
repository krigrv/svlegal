import os
from functools import lru_cache

import gradio as gr
from llama_cpp import Llama
from dotenv import load_dotenv


load_dotenv()


SYSTEM_PROMPT = """You are SV Legal AI, an Indian legal drafting and research assistant for a lawyer's internal educational use.
You help with legal notices, issue spotting, case briefs, client emails, clause review, compliance checklists, and research memos.
Do not claim to be a lawyer. Do not present output as final legal advice.
Use Indian legal context by default. If jurisdiction, dates, parties, forum, value, limitation, or key facts are missing, ask for them briefly before making strong conclusions.
Prefer structured, lawyer-ready output with concise headings, numbered clauses where useful, and practical next steps.
If you are unsure about a section number, citation, limitation period, or current legal position, say it must be verified from an official source.
Never invent case citations. Mark placeholders clearly in square brackets.
"""


APP_CSS = """
.gradio-container {
    background:
        radial-gradient(circle at top left, rgba(179, 139, 77, 0.16), transparent 32%),
        linear-gradient(180deg, #0b1220 0%, #0f172a 100%);
}

.ai-shell {
    max-width: 1240px;
    margin: 0 auto;
}

.ai-hero {
    padding: 1rem 0 0.5rem;
}

.ai-kicker {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.8rem;
    border: 1px solid rgba(179, 139, 77, 0.35);
    border-radius: 999px;
    color: #f5d28c;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.9rem;
    background: rgba(255, 255, 255, 0.03);
}

.ai-title h1 {
    color: #f8f7f3;
    font-size: clamp(2rem, 4vw, 3.75rem);
    line-height: 1.05;
    margin-bottom: 0.8rem;
}

.ai-title p {
    color: rgba(255, 255, 255, 0.72);
    max-width: 72ch;
    margin-bottom: 0;
    font-size: 1rem;
    line-height: 1.8;
}

.ai-panel {
    background: rgba(14, 20, 33, 0.86);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
    backdrop-filter: blur(16px);
}

.ai-panel--info {
    padding: 1.2rem;
}

.ai-panel--chat {
    padding: 1rem;
}

.ai-facts {
    display: grid;
    gap: 0.75rem;
    margin-top: 1rem;
}

.ai-fact {
    padding: 0.9rem 1rem;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    color: rgba(255, 255, 255, 0.82);
}

.ai-fact strong {
    display: block;
    color: #fff;
    margin-bottom: 0.25rem;
}

.ai-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: 1rem;
}

.ai-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.45rem 0.8rem;
    border-radius: 999px;
    border: 1px solid rgba(179, 139, 77, 0.28);
    color: #d9c08a;
    font-size: 0.75rem;
    letter-spacing: 0.04em;
}

.ai-step-list {
    margin: 0;
    padding-left: 1.2rem;
    color: rgba(255, 255, 255, 0.82);
}

.ai-step-list li {
    margin-bottom: 0.65rem;
}

.ai-inline-code {
    display: inline-block;
    padding: 0.2rem 0.45rem;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.06);
    color: #f3dfb5;
    font-size: 0.92em;
}

.ai-chat .gradio-container .chatbot, .ai-chat .gradio-container .wrap {
    background: rgba(255, 255, 255, 0.03);
}

.ai-chat .gradio-container textarea, .ai-chat .gradio-container input {
    background: rgba(255, 255, 255, 0.04) !important;
    color: #fff !important;
    border-color: rgba(255, 255, 255, 0.08) !important;
}

.ai-chat .gradio-container button {
    border-radius: 999px !important;
}

.ai-note {
    margin-top: 1rem;
    color: rgba(255, 255, 255, 0.55);
    font-size: 0.82rem;
}
"""


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@lru_cache(maxsize=1)
def load_llm() -> Llama:
    model_path = os.getenv("MODEL_PATH")
    if not model_path:
        raise RuntimeError(
            "MODEL_PATH is not set. Point it at your GGUF file, for example: ./models/llama-3.2-1b-instruct.Q4_K_M.gguf"
        )

    if not os.path.exists(model_path):
        raise RuntimeError(f"Model file not found: {model_path}")

    return Llama(
        model_path=model_path,
        n_ctx=env_int("N_CTX", 4096),
        n_gpu_layers=env_int("N_GPU_LAYERS", 0),
        chat_format="llama-3",
        verbose=False,
    )


def respond(message, history, temperature, max_tokens):
    llm = load_llm()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for user_message, assistant_message in history:
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": assistant_message})
    messages.append({"role": "user", "content": message})

    result = llm.create_chat_completion(
        messages=messages,
        temperature=temperature,
        top_p=0.9,
        max_tokens=max_tokens,
    )

    return result["choices"][0]["message"]["content"]


def chat(message, history, temperature, max_tokens):
    history = history or []
    response = respond(message, history, temperature, max_tokens)
    history = history + [(message, response)]
    return history, ""


with gr.Blocks(
    title="SV Legal AI Lab",
    theme=gr.themes.Soft(),
    css=APP_CSS,
) as demo:
    with gr.Column(elem_classes="ai-shell"):
        gr.Markdown(
            """
            <div class="ai-hero">
              <div class="ai-kicker">Local GGUF model • Educational legal assistant</div>
              <div class="ai-title">
                <h1>Ambuj Legal LLM starter</h1>
                <p>
                  A polished local chat workspace for <code>invincibleambuj/Ambuj-Tripathi-Indian-Legal-Llama-GGUF</code>.
                  Use it for Indian legal issue spotting, drafting support, and quick research prompts.
                </p>
              </div>
            </div>
            """
        )

        with gr.Row(equal_height=True):
            with gr.Column(scale=1, elem_classes="ai-panel ai-panel--info"):
                gr.Markdown("### What this model is for")
                gr.Markdown(
                    """
                    - Indian legal Q&A
                    - Drafting assistance
                    - Summaries of statutes and procedures
                    - Internal legal knowledge lookup
                    """
                )

                gr.Markdown("### Quick start")
                gr.Markdown(
                    """
                    1. Download the GGUF file into `./models`
                    2. Run `./run.sh`
                    3. Open the local browser link
                    """
                )

                gr.Markdown("### Model facts")
                with gr.Column(elem_classes="ai-facts"):
                    gr.Markdown(
                        """
                        <div class="ai-fact">
                          <strong>Repo</strong>
                          invincibleambuj/Ambuj-Tripathi-Indian-Legal-Llama-GGUF
                        </div>
                        <div class="ai-fact">
                          <strong>Format</strong>
                          GGUF, Q4_K_M quantization
                        </div>
                        <div class="ai-fact">
                          <strong>Use case</strong>
                          Local, CPU-friendly legal assistant
                        </div>
                        """
                    )

                gr.Markdown("### Try prompts")
                gr.Markdown(
                    """
                    - `Explain the likely issues in a consumer dispute and list the documents to collect.`
                    - `Draft a short legal notice for payment default in India.`
                    - `Summarize the main points of the Indian Constitution article relevant to equality.`
                    """
                )
                gr.Markdown(
                    """
                    <div class="ai-note">
                      This assistant is for educational use only and is not legal advice.
                    </div>
                    """
                )

            with gr.Column(scale=1.45, elem_classes="ai-panel ai-panel--chat ai-chat"):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=620,
                    show_copy_button=True,
                    bubble_full_width=False,
                )
                message = gr.Textbox(
                    label="Ask the model",
                    placeholder="Type an Indian legal question or drafting request...",
                    lines=3,
                )
                with gr.Row():
                    temperature = gr.Slider(0.0, 1.0, value=0.35, step=0.05, label="Temperature")
                    max_tokens = gr.Slider(64, 1024, value=512, step=32, label="Max tokens")
                with gr.Row():
                    send = gr.Button("Send", variant="primary")
                    clear = gr.Button("Clear chat")

                message.submit(
                    chat,
                    inputs=[message, chatbot, temperature, max_tokens],
                    outputs=[chatbot, message],
                )
                send.click(
                    chat,
                    inputs=[message, chatbot, temperature, max_tokens],
                    outputs=[chatbot, message],
                )
                clear.click(lambda: ([], ""), outputs=[chatbot, message])

        gr.Markdown(
            """
            <div class="ai-note">
              Tip: use the provided `run.sh` to install dependencies, configure the model path, and launch the app in one step.
            </div>
            """
        )


if __name__ == "__main__":
    demo.queue()
    demo.launch(
        server_name="0.0.0.0",
        server_port=env_int("PORT", 7860),
        show_error=True,
    )
