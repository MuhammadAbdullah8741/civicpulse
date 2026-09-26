import { afterEach, expect, it, vi } from 'vitest';
import { api } from '../src/api/client';
afterEach(() => vi.unstubAllGlobals());
it('reads statistics cache state from the response header', async () => {
  const data={total:0,by_category:{},by_priority:{},by_status:{}};
  const fetchMock=vi.fn().mockResolvedValue(new Response(JSON.stringify(data),{headers:{'X-Cache':'HIT'}}));
  vi.stubGlobal('fetch',fetchMock);
  expect(await api.stats()).toEqual({data,cache:'HIT'});
  expect(fetchMock.mock.calls[0][0]).toBe('/api/stats');
});
it('uses the relative provider metadata endpoint', async () => {
  const data={active_provider:'simulated',cache_ttl_seconds:86400,triage_requests:0,cache_hits:0,cache_hit_rate:0,recent_outcomes:[]};
  const fetchMock=vi.fn().mockResolvedValue(new Response(JSON.stringify(data)));
  vi.stubGlobal('fetch',fetchMock);
  expect(await api.providers()).toEqual(data);
  expect(fetchMock.mock.calls[0][0]).toBe('/api/meta/providers');
});
