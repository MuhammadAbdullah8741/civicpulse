import { afterEach, expect, it, vi } from 'vitest';
import { api, ApiError } from '../src/api/client';
afterEach(() => vi.unstubAllGlobals());

it('uses a relative API path and serializes filters', async () => {
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({items: [], total: 0, page: 2, page_size: 10})));
  vi.stubGlobal('fetch', fetchMock);
  await api.list({category: 'water', page: 2, page_size: 10});
  const path = fetchMock.mock.calls[0][0] as string;
  expect(path).toMatch(/^\/api\/complaints\?/);
  expect(new URLSearchParams(path.split('?')[1]).get('category')).toBe('water');
  expect(new URLSearchParams(path.split('?')[1]).get('page')).toBe('2');
});
it('preserves the server conflict message verbatim', async () => {
  const message = 'Invalid status transition: resolved -> open';
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({detail: message}), {status: 409})));
  await expect(api.update('test-id', 'open')).rejects.toThrow(message);
});
it('preserves retry-after on rate limiting', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({detail: 'Too many requests'}), {status: 429, headers: {'Retry-After': '31'}})));
  const error = await api.create({text: 'Water pipe leaking outside', location: 'Test street'}).catch(e => e);
  expect(error).toBeInstanceOf(ApiError);
  expect(error.status).toBe(429);
  expect(error.retryAfter).toBe('31');
});
it('handles a non-JSON upstream failure', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('Bad gateway', {status: 502})));
  await expect(api.get('test-id')).rejects.toThrow('Request failed (502). Please try again.');
});
