// Node 22+, no dependencies. Default mode reads only; --write creates one synthetic report.
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';

const base = (process.env.FRONTEND_URL || 'http://127.0.0.1:8080').replace(/\/$/, '');
async function request(path, options = {}, expected = 200) {
  const response = await fetch(`${base}${path}`, {
    ...options,
    signal: AbortSignal.timeout(15000),
  });
  assert.equal(response.status, expected, `${path}: expected HTTP ${expected}, got ${response.status}`);
  return response;
}
async function json(path, options = {}, expected = 200) {
  const response = await request(path, options, expected);
  assert.match(response.headers.get('content-type') || '', /application\/json/, `${path}: expected JSON`);
  return response.json();
}
function body(method, data) {
  return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) };
}

assert.equal((await (await request('/health')).text()).trim(), 'ok');
const html = await (await request('/')).text();
assert.match(html, /<div[^>]*id="root"/);
const script = html.match(/<script[^>]*src="(\/assets\/[^"?]+\.js)"/);
assert.ok(script, 'Built JavaScript asset must appear in index.html');
assert.match((await request(script[1])).headers.get('content-type') || '', /javascript/);
const list = await json('/api/complaints?page=1&page_size=1');
assert.ok(Array.isArray(list.items));
assert.ok(Number.isInteger(list.total));
const statsResponse = await request('/api/stats');
assert.ok(['HIT', 'MISS'].includes(statsResponse.headers.get('x-cache')), 'Proxy must preserve X-Cache');
const stats = await statsResponse.json();
assert.ok(Number.isInteger(stats.total));
const metadata = await json('/api/meta/providers');
assert.equal(typeof metadata.active_provider, 'string');
assert.ok(Array.isArray(metadata.recent_outcomes));
console.log('PASS: frontend health, HTML, JavaScript asset, API list, stats cache header and provider metadata');

if (process.argv.includes('--write')) {
  const marker = randomUUID();
  const created = await json('/api/complaints', body('POST', {
    text: `Burst water pipe flooding the road. Synthetic CI smoke report ${marker}.`,
    location: 'Synthetic CI test street',
    reporter_contact: null,
  }), 201);
  assert.match(created.id, /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i);
  assert.equal(created.status, 'open');
  assert.ok(created.allowed_transitions.includes('in_progress'));
  const path = `/api/complaints/${created.id}`;
  assert.equal((await json(path)).id, created.id);
  const updated = await json(`${path}/status`, body('PATCH', {status: 'in_progress'}));
  assert.equal(updated.status, 'in_progress');
  const resolved = await json(`${path}/status`, body('PATCH', {status: 'resolved'}));
  assert.equal(resolved.status, 'resolved');
  assert.deepEqual(resolved.allowed_transitions, []);
  await request(`${path}/status`, body('PATCH', {status: 'open'}), 409);
  assert.equal((await json(path)).status, 'resolved');
  console.log(`PASS: create, fetch, status transitions and terminal conflict through nginx; synthetic report ${created.id}`);
}
