import type { components } from './schema';

export type Complaint = components['schemas']['ComplaintResponse'];
export type ComplaintInput = components['schemas']['ComplaintCreate'];
export type ComplaintPage = components['schemas']['ComplaintPage'];
export type Status = components['schemas']['Status'];
export type Category = components['schemas']['Category'];
export type Priority = components['schemas']['Priority'];
export type Filters = {page?: number; page_size?: number; category?: Category; priority?: Priority; status?: Status};

export type FieldError = {field: string; message: string};
function fieldErrors(body: unknown): FieldError[] {
  if (!body || typeof body !== 'object' || !('errors' in body) || !Array.isArray(body.errors)) return [];
  return body.errors.filter((item): item is FieldError =>
    item !== null && typeof item === 'object' && typeof item.field === 'string' && typeof item.message === 'string');
}
export class ApiError extends Error {
  constructor(message: string, public status: number, public retryAfter: string | null, public fields: FieldError[] = []) {
    super(message);
    this.name = 'ApiError';
  }
}
function detailMessage(body: unknown, status: number): string {
  if (typeof body === 'object' && body !== null && 'detail' in body && typeof body.detail === 'string') return body.detail;
  return `Request failed (${status}). Please try again.`;
}
async function requestWithHeaders<T>(path: string, options: RequestInit = {}): Promise<{data: T; headers: Headers}> {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(detailMessage(body, response.status), response.status, response.headers.get('Retry-After'), fieldErrors(body));
  if (body === null) throw new ApiError('The server returned an empty or invalid response.', response.status, null);
  return {data: body as T, headers: response.headers};
}
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  return (await requestWithHeaders<T>(path, options)).data;
}
export type StatsData = components['schemas']['StatsResponse'];
export type ProviderMetadata = components['schemas']['ProviderMetadata'];
export type StatsResult = {data: StatsData; cache: string | null};
export const api = {
  stats: async (): Promise<StatsResult> => {
    const result = await requestWithHeaders<StatsData>('/api/stats');
    return {data: result.data, cache: result.headers.get('X-Cache')};
  },
  providers: () => request<ProviderMetadata>('/api/meta/providers'),
  create: (body: ComplaintInput) => request<Complaint>('/api/complaints', {method: 'POST', body: JSON.stringify(body)}),
  get: (id: string) => request<Complaint>(`/api/complaints/${encodeURIComponent(id)}`),
  list: (filters: Filters = {}) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) if (value !== undefined) params.set(key, String(value));
    return request<ComplaintPage>(`/api/complaints?${params}`);
  },
  update: (id: string, status: Status) => request<Complaint>(`/api/complaints/${encodeURIComponent(id)}/status`, {method: 'PATCH', body: JSON.stringify({status})}),
};
