module.exports = async function handler(request, response) {
  if (request.method !== 'GET') {
    response.setHeader('Allow', 'GET');
    return response.status(405).json({ detail: 'Method not allowed' });
  }

  const hfEndpoint = (process.env.LEGAL_AI_HF_ENDPOINT_URL || '').replace(/\/$/, '');
  const backendUrl = (process.env.LEGAL_AI_BACKEND_URL || '').replace(/\/$/, '');
  if (!hfEndpoint && !backendUrl) {
    return response.status(503).json({
      status: 'missing_config',
      detail: 'Configure LEGAL_AI_HF_ENDPOINT_URL or LEGAL_AI_BACKEND_URL.',
    });
  }

  return response.status(200).json({
    status: 'configured',
    provider: hfEndpoint ? 'huggingface' : 'backend',
  });
};
