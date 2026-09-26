import { afterEach, expect, it, vi } from 'vitest';
import { api, ApiError } from '../src/api/client';
afterEach(() => vi.unstubAllGlobals());
it('retains valid field errors and ignores malformed error entries', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
    detail: 'Validation failed', errors: [{field:'body.text', message:'Too short'}, null, {field:4}],
  }), {status:400})));
  const error = await api.create({text:'short', location:'Test street'}).catch(e => e);
  expect(error).toBeInstanceOf(ApiError);
  expect(error.fields).toEqual([{field:'body.text', message:'Too short'}]);
});
