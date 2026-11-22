import type { ApiResponse } from './types'

export class ApiRequestError extends Error {
  code: string;
  hint?: string;

  constructor(message: string, code: string = 'API_ERROR', hint?: string) {
    super(message);
    this.name = 'ApiRequestError';
    this.code = code;
    this.hint = hint;
  }
}

export async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const url = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  const payload: ApiResponse<T> = await response.json();

  if (!payload.ok) {
    throw new ApiRequestError(
      payload.error?.message || 'API request failed',
      payload.error?.code || 'UNKNOWN_ERROR',
      payload.error?.hint
    );
  }

  return payload;
}
