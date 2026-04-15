async function readJson(request) {
  if (request.body && typeof request.body === 'object') {
    return request.body;
  }

  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
  }

  const rawBody = Buffer.concat(chunks).toString('utf8');
  return rawBody ? JSON.parse(rawBody) : {};
}

const WORKFLOW_PROMPTS = {
  general: 'Answer as a concise legal assistant. Give assumptions, analysis, and next steps.',
  legal_notice:
    'Draft a formal Indian legal notice. Include parties, facts, demand, timeline to comply, consequences of non-compliance, and placeholders for missing details.',
  case_brief:
    'Prepare a case brief. Use: Facts, Issues, Applicable Law To Verify, Arguments For Client, Risks, Evidence Needed, Next Steps.',
  clause_review:
    'Review the clause or contract extract. Use: Concern, Risk Level, Why It Matters, Suggested Revision, Negotiation Note.',
  research_memo:
    'Prepare a short research memo. Use: Question Presented, Short Answer, Legal Position To Verify, Analysis, Practical Recommendation.',
  client_email:
    'Draft a polished client email. Keep it professional, clear, and cautious. Include caveats and action items.',
  compliance_checklist:
    'Create a compliance checklist. Group by immediate, short-term, and ongoing actions with owner/document columns where useful.',
  document_summary:
    'Summarize the supplied document or facts. Use: Executive Summary, Key Points, Risks, Missing Information, Questions For Client.',
};

function buildMessages(body) {
  const workflow = WORKFLOW_PROMPTS[body.workflow] || WORKFLOW_PROMPTS.general;
  const messages = [
    {
      role: 'system',
      content:
        'You are SV Legal AI, an Indian legal drafting and research assistant for a lawyer\'s internal educational use. ' +
        'You help with legal notices, issue spotting, case briefs, client emails, clause review, compliance checklists, and research memos. ' +
        'Do not claim to be a lawyer. Do not present output as final legal advice. ' +
        'Use Indian legal context by default. If jurisdiction, dates, parties, forum, value, limitation, or key facts are missing, ask for them briefly before making strong conclusions. ' +
        'Prefer structured, lawyer-ready output with concise headings, numbered clauses where useful, and practical next steps. ' +
        'If you are unsure about a section number, citation, limitation period, or current legal position, say it must be verified from an official source. ' +
        'Never invent case citations. Mark placeholders clearly in square brackets. ' +
        `Current work product mode: ${workflow}`,
    },
  ];

  if (Array.isArray(body.history)) {
    for (const item of body.history) {
      if (item && (item.role === 'user' || item.role === 'assistant') && typeof item.content === 'string') {
        messages.push({ role: item.role, content: item.content });
      }
    }
  }

  messages.push({ role: 'user', content: body.message || '' });
  return messages;
}

function resolveProvider() {
  const hfEndpoint = (process.env.LEGAL_AI_HF_ENDPOINT_URL || '').replace(/\/$/, '');
  const hfToken = process.env.LEGAL_AI_HF_TOKEN || process.env.HF_TOKEN || '';
  if (hfEndpoint) {
    return { type: 'huggingface', url: `${hfEndpoint}/v1/chat/completions`, token: hfToken };
  }

  const backendUrl = (process.env.LEGAL_AI_BACKEND_URL || '').replace(/\/$/, '');
  const backendToken = process.env.LEGAL_AI_BACKEND_TOKEN || '';
  if (backendUrl) {
    return { type: 'backend', url: `${backendUrl}/api/legal-ai`, token: backendToken };
  }

  return null;
}

module.exports = async function handler(request, response) {
  if (request.method !== 'POST') {
    response.setHeader('Allow', 'POST');
    return response.status(405).json({ detail: 'Method not allowed' });
  }

  const provider = resolveProvider();
  if (!provider) {
    return response.status(503).json({
      detail:
        'Configure LEGAL_AI_HF_ENDPOINT_URL and LEGAL_AI_HF_TOKEN in Vercel, or LEGAL_AI_BACKEND_URL for the legacy backend.',
    });
  }

  try {
    const body = await readJson(request);
    const headers = { 'Content-Type': 'application/json' };
    if (provider.token) {
      headers.Authorization = `Bearer ${provider.token}`;
    }

    const upstreamBody =
      provider.type === 'huggingface'
        ? JSON.stringify({
            messages: buildMessages(body),
            temperature: body.temperature ?? 0.35,
            max_tokens: body.max_tokens ?? 768,
            top_p: 0.9,
            stream: false,
          })
        : JSON.stringify(body);

    const upstream = await fetch(provider.url, {
      method: 'POST',
      headers,
      body: upstreamBody,
    });

    const data = await upstream.json().catch(() => ({
      detail: 'Model backend returned a non-JSON response.',
    }));

    if (provider.type === 'huggingface') {
      const answer =
        data?.choices?.[0]?.message?.content ||
        data?.choices?.[0]?.text ||
        data?.generated_text ||
        '';
      if (!answer) {
        return response.status(502).json({
          detail: 'Hugging Face endpoint did not return usable text.',
          upstream: data,
        });
      }
      return response.status(upstream.status).json({
        answer,
        model_repo: data.model || 'invincibleambuj/Ambuj-Tripathi-Indian-Legal-Llama-GGUF',
        provider: 'huggingface',
      });
    }

    return response.status(upstream.status).json(data);
  } catch (error) {
    console.error('Legal AI proxy failed:', error);
    return response.status(500).json({
      detail: 'Legal AI proxy failed. Check Vercel logs and the model backend.',
    });
  }
};
