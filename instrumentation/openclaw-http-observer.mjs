import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const OBS_URL = process.env.OPENCLAW_LLM_OBS_URL || 'http://127.0.0.1:8091/api/v1/llm-calls';
const DEBUG_LOG = process.env.OPENCLAW_LLM_OBS_DEBUG_LOG || path.join(os.homedir(), '.openclaw', 'logs', 'http-observer.log');
const INCLUDE_HINTS = (process.env.OPENCLAW_LLM_OBS_HOST_HINTS || 'copilot,openai,anthropic,openrouter,googleapis').split(',').map(s => s.trim()).filter(Boolean);
const EXCLUDE_HINTS = (process.env.OPENCLAW_LLM_OBS_EXCLUDE_HINTS || '127.0.0.1:8091,localhost:8091,discord.com,discordapp.com,api.telegram.org').split(',').map(s => s.trim()).filter(Boolean);

fs.mkdirSync(path.dirname(DEBUG_LOG), { recursive: true });

const originalFetch = globalThis.fetch?.bind(globalThis);
if (!originalFetch) {
  fs.appendFileSync(DEBUG_LOG, `[${new Date().toISOString()}] fetch missing; observer not installed\n`);
} else {
  function shouldExclude(url) {
    return EXCLUDE_HINTS.some(h => url.includes(h));
  }

  function shouldCapture(url, bodyText) {
    if (shouldExclude(url)) return false;
    const hay = `${url}\n${bodyText || ''}`.toLowerCase();
    return INCLUDE_HINTS.some(h => hay.includes(h.toLowerCase())) || /\/v1\/(chat\/completions|responses|messages)/i.test(url);
  }

  function parseUsage(provider, data) {
    const usage = data?.usage || {};
    if (provider === 'anthropic') {
      const input = usage.input_tokens ?? null;
      const output = usage.output_tokens ?? null;
      const cacheRead = usage.cache_read_input_tokens ?? null;
      const uncached = input != null && cacheRead != null ? Math.max(0, input - cacheRead) : null;
      return {
        input_tokens: input,
        input_cached_tokens: cacheRead,
        input_uncached_tokens: uncached,
        output_tokens: output,
        total_tokens: input != null && output != null ? input + output : null,
      };
    }
    const input = usage.input_tokens ?? usage.prompt_tokens ?? null;
    const output = usage.output_tokens ?? usage.completion_tokens ?? null;
    const total = usage.total_tokens ?? (input != null && output != null ? input + output : null);
    const details = usage.input_tokens_details || usage.prompt_tokens_details || {};
    const cached = details.cached_tokens ?? details.cache_read_tokens ?? null;
    const uncached = input != null && cached != null ? Math.max(0, input - cached) : null;
    return {
      input_tokens: input,
      input_cached_tokens: cached,
      input_uncached_tokens: uncached,
      output_tokens: output,
      total_tokens: total,
    };
  }

  function guessProvider(url) {
    const low = url.toLowerCase();
    if (low.includes('anthropic')) return 'anthropic';
    if (low.includes('copilot')) return 'github-copilot';
    if (low.includes('openai')) return 'openai';
    if (low.includes('openrouter')) return 'openrouter';
    if (low.includes('googleapis') || low.includes('gemini')) return 'google';
    return 'unknown';
  }

  function extractPromptText(body) {
    if (!body || typeof body !== 'object') return null;
    if (typeof body.input === 'string') return body.input;
    if (Array.isArray(body.messages)) {
      const parts = [];
      for (const msg of body.messages) {
        const content = msg?.content;
        if (typeof content === 'string') parts.push(content);
        else if (Array.isArray(content)) {
          for (const item of content) {
            if (item && typeof item.text === 'string') parts.push(item.text);
          }
        }
      }
      return parts.join('\n\n') || null;
    }
    return null;
  }

  function extractResponseText(body) {
    if (!body || typeof body !== 'object') return null;
    if (typeof body.output_text === 'string') return body.output_text;
    if (Array.isArray(body.content)) {
      return body.content.map(x => x?.text).filter(Boolean).join('\n\n') || null;
    }
    if (Array.isArray(body.choices)) {
      return body.choices.map(x => x?.message?.content).filter(Boolean).join('\n\n') || null;
    }
    if (Array.isArray(body.output)) {
      const parts = [];
      for (const item of body.output) {
        for (const c of item?.content || []) {
          if (typeof c?.text === 'string') parts.push(c.text);
        }
      }
      return parts.join('\n\n') || null;
    }
    return null;
  }

  globalThis.fetch = async function observedFetch(input, init) {
    const req = input instanceof Request ? input.clone() : new Request(input, init);
    const url = req.url;
    const method = req.method || 'GET';
    const started = Date.now();
    let requestBodyText = '';
    let requestJson = null;
    try {
      requestBodyText = await req.text();
      requestJson = requestBodyText ? JSON.parse(requestBodyText) : null;
    } catch {}

    const capture = shouldCapture(url, requestBodyText);
    const response = await originalFetch(input, init);
    if (!capture) return response;

    let responseText = '';
    let responseJson = null;
    try {
      responseText = await response.clone().text();
      responseJson = responseText ? JSON.parse(responseText) : null;
    } catch {}

    const provider = guessProvider(url);
    const usage = parseUsage(provider, responseJson || {});
    const payload = {
      trace_id: responseJson?.id || null,
      created_at: new Date(started).toISOString(),
      finished_at: new Date().toISOString(),
      latency_ms: Date.now() - started,
      provider,
      model: responseJson?.model || requestJson?.model || null,
      status: response.ok ? 'ok' : 'error',
      error_type: response.ok ? null : `http_${response.status}`,
      error_message: response.ok ? null : responseText.slice(0, 2000),
      prompt_text: extractPromptText(requestJson),
      response_text: extractResponseText(responseJson),
      request_json: requestJson || { raw: requestBodyText.slice(0, 4000) },
      response_json: responseJson || { raw: responseText.slice(0, 4000) },
      metadata_json: {
        source: 'http-observer',
        url,
        method,
        status_code: response.status,
      },
      ...usage,
    };

    try {
      fs.appendFileSync(DEBUG_LOG, JSON.stringify({ ts: new Date().toISOString(), provider, url, model: payload.model, prompt: payload.prompt_text?.slice(0, 160), status: payload.status }) + '\n');
    } catch {}

    try {
      await originalFetch(OBS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (err) {
      try {
        fs.appendFileSync(DEBUG_LOG, `[${new Date().toISOString()}] post_failed ${String(err)}\n`);
      } catch {}
    }

    return response;
  };

  fs.appendFileSync(DEBUG_LOG, `[${new Date().toISOString()}] http observer installed\n`);
}
