// Compare the consumed API schemas against a running backend; ignores new endpoints.
import { readFile } from 'node:fs/promises';
const url = process.env.OPENAPI_URL || 'http://127.0.0.1:8000/openapi.json';
const expected = JSON.parse(await readFile(new URL('../openapi.json', import.meta.url), 'utf8'));
function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k => [k, stable(value[k])]));
  return value;
}
const response = await fetch(url, {signal: AbortSignal.timeout(10000)});
if (!response.ok) throw new Error(`OpenAPI returned ${response.status}`);
const actual = await response.json();
for (const [name, schema] of Object.entries(expected.components.schemas)) {
  if (JSON.stringify(stable(schema)) !== JSON.stringify(stable(actual.components?.schemas?.[name]))) {
    throw new Error(`Backend schema changed: ${name}. Review the contract and regenerate types.`);
  }
}
for (const [path, operations] of Object.entries(expected.paths)) {
  for (const [method, operation] of Object.entries(operations)) {
    const current = actual.paths?.[path]?.[method];
    if (!current) throw new Error(`Missing backend operation: ${method} ${path}`);
    for (const key of ['parameters', 'requestBody', 'responses']) {
      if (JSON.stringify(stable(operation[key])) !== JSON.stringify(stable(current[key]))) {
        throw new Error(`Backend contract changed: ${method} ${path} (${key})`);
      }
    }
  }
}
console.log('Frontend API contracts match the running backend.');
