import type { components } from './schema';

export type Complaint = components['schemas']['ComplaintResponse'];
export type ComplaintInput = components['schemas']['ComplaintCreate'];
export type ComplaintPage = components['schemas']['ComplaintPage'];
export type Status = components['schemas']['Status'];
export type Category = components['schemas']['Category'];
export type Priority = components['schemas']['Priority'];
export type Filters = {page?: number; page_size?: number; category?: Category; priority?: Priority; status?: Status};

export class ApiError extends Error {
  constructor(message: string, public status: number, public retryAfter: string | null) {
    super(message);
    this.name = 'ApiError';
  }
}
function detailMessage(body: unknown, status: number): string {
  if (typeof body === 'object' && body !== null && 'detail' in body && typeof body.detail === 'string') return body.detail;
  return `Request failed (${status}). Please try again.`;
}
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(detailMessage(body, response.status), response.status, response.headers.get('Retry-After'));
  if (body === null) throw new ApiError('The server returned an empty or invalid response.', response.status, null);
  return body as T;
}
export const api = {
  create: (body: ComplaintInput) => request<Complaint>('/api/complaints', {method: 'POST', body: JSON.stringify(body)}),
  get: (id: string) => request<Complaint>(`/api/complaints/${encodeURIComponent(id)}`),
  list: (filters: Filters = {}) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) if (value !== undefined) params.set(key, String(value));
    return request<ComplaintPage>(`/api/complaints?${params}`);
  },
  update: (id: string, status: Status) => request<Complaint>(`/api/complaints/${encodeURIComponent(id)}/status`, {method: 'PATCH', body: JSON.stringify({status})}),
};
