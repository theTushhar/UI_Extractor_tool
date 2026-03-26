const BASE_URL = 'http://localhost:8000';

const maskApiKey = (apiKey: string) => {
  if (!apiKey) return '(missing)';
  if (apiKey.length <= 8) return '***';
  return `${apiKey.slice(0, 4)}...${apiKey.slice(-4)}`;
};

const logRequest = (label: string, payload?: unknown) => {
  console.debug(`[api] ${label}`, payload ?? '');
};

const parseJsonSafely = async (response: Response) => {
  try {
    return await response.json();
  } catch (error) {
    console.error('[api] Failed to parse JSON response', error);
    return null;
  }
};

const postJson = async (path: string, body?: Record<string, unknown>) => {
  const startedAt = performance.now();
  const requestUrl = `${BASE_URL}${path}`;
  logRequest(`POST ${path} -> request`, body);

  try {
    const response = await fetch(requestUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    const data = await parseJsonSafely(response);
    const durationMs = Math.round(performance.now() - startedAt);
    logRequest(`POST ${path} -> response ${response.status} (${durationMs}ms)`, data);

    if (!response.ok) {
      throw new Error(data?.detail || `Request failed with status ${response.status}`);
    }

    return data;
  } catch (error) {
    console.error(`[api] POST ${path} failed`, error);
    throw error;
  }
};

export const api = {
  openBrowser: async (url: string) => {
    return postJson('/open-browser', { url });
  },

  closeBrowser: async () => {
    return postJson('/close-browser');
  },

  scanPage: async (goal: string, apiKey: string, model: string) => {
    logRequest('scanPage metadata', {
      goalPreview: goal.slice(0, 80),
      model,
      apiKey: maskApiKey(apiKey),
    });
    return postJson('/scan-page', { goal, api_key: apiKey, model });
  },

  highlightElement: async (selector: string) => {
    return postJson('/highlight-element', { selector });
  },
};
