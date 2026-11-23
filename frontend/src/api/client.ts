import type { ApiResponse } from './types'

export class ApiRequestError extends Error {
  code: string;
  hint?: string;
  status?: number;
  data?: any;

  constructor(message: string, code: string = 'API_ERROR', hint?: string, status?: number, data?: any) {
    super(message);
    this.name = 'ApiRequestError';
    this.code = code;
    this.hint = hint;
    this.status = status;
    this.data = data;
  }
}

export async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const url = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  const { headers, ...restOptions } = options || {};
  const isFormData = typeof FormData !== 'undefined' && restOptions.body instanceof FormData;

  const defaultHeaders: Record<string, string> = isFormData
    ? {}
    : { 'Content-Type': 'application/json' };

  const mergedHeaders: Record<string, string> = {
    ...defaultHeaders,
    ...((headers as Record<string, string>) || {}),
  };

  try {
    const response = await fetch(url, {
      ...restOptions,
      headers: mergedHeaders,
    });

    let payload: any;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      try {
        payload = await response.json();
      } catch {
        payload = null;
      }
    } else {
      const text = await response.text();
      payload = { ok: false, error: { message: text || `HTTP ${response.status}` } };
    }

    if (!response.ok || (payload && payload.ok === false)) {
      const detailMsg = Array.isArray(payload?.detail)
        ? payload.detail.map((d: any) => `${d.loc?.slice(-1)[0] || 'field'}: ${d.msg}`).join(', ')
        : (typeof payload?.detail === 'string' ? payload.detail : null);

      const errorMessage =
        payload?.error?.message ||
        detailMsg ||
        (payload?.message ? String(payload.message) : null) ||
        (response.statusText ? `HTTP ${response.status}: ${response.statusText}` : 'API request failed');

      const errorCode = payload?.error?.code || `HTTP_${response.status}`;
      const hint = payload?.error?.hint;

      console.error(`[API Error] ${options?.method || 'GET'} ${url} (Status ${response.status}):`, {
        error: errorMessage,
        code: errorCode,
        hint,
        data: payload,
      });

      throw new ApiRequestError(errorMessage, errorCode, hint, response.status, payload);
    }

    return payload as ApiResponse<T>;
  } catch (err: any) {
    console.error(`[fetchApi Network/Client Error] ${url}:`, err);
    throw err;
  }
}
