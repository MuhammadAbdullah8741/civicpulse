import { useCallback, useEffect, useRef, useState } from 'react';
import { api, type ProviderMetadata, type StatsResult } from '../api/client';
import './stats.css';

const errorText = (error: unknown) => error instanceof Error ? error.message : 'Request failed. Please retry.';
export function Stats() {
  const [stats, setStats] = useState<StatsResult | null>(null);
  const [meta, setMeta] = useState<ProviderMetadata | null>(null);
  const [statsError, setStatsError] = useState('');
  const [metaError, setMetaError] = useState('');
  const [loading, setLoading] = useState(true);
  const sequence = useRef(0);
  const refresh = useCallback(async () => {
    const current = ++sequence.current;
    setLoading(true); setStatsError(''); setMetaError('');
    const [counts, history] = await Promise.allSettled([api.stats(), api.providers()]);
    if (current !== sequence.current) return;
    if (counts.status === 'fulfilled') setStats(counts.value);
    else {setStats(null);setStatsError(errorText(counts.reason));}
    if (history.status === 'fulfilled') setMeta(history.value);
    else {setMeta(null);setMetaError(errorText(history.reason));}
    setLoading(false);
  }, []);
  useEffect(() => {void refresh();return () => {sequence.current += 1;};}, [refresh]);
  const cache = stats?.cache === 'HIT' || stats?.cache === 'MISS' ? stats.cache : 'UNKNOWN';
  return <section aria-labelledby="stats-title">
    <div className="section-head"><div><span className="eyebrow">CITY SNAPSHOT</span>
      <h2 id="stats-title">Your city at a glance</h2></div>
      <button className="secondary" disabled={loading} onClick={() => void refresh()}>Refresh statistics</button></div>
    {loading && <p role="status">Loading statistics and provider history…</p>}
    {statsError && <p role="alert" className="error">Statistics: {statsError}</p>}
    {metaError && <p role="alert" className="error">Provider history: {metaError}</p>}
    <div className="metrics">
      <article className="panel" aria-label="Total reports"><span>Total reports</span><strong>{stats?.data.total ?? '—'}</strong></article>
      <article className="panel" aria-label="High priority reports"><span>High priority</span><strong>{stats?.data.by_priority.high ?? '—'}</strong></article>
      <article className="panel" aria-label="Statistics cache"><span>Statistics cache</span><strong className="small-value">{stats ? cache : '—'}</strong><small>Actual X-Cache response header</small></article>
      <article className="panel" aria-label="Triage cache hit rate"><span>Triage cache hit rate</span><strong>{meta ? `${(meta.cache_hit_rate * 100).toFixed(1)}%` : '—'}</strong><small>{meta ? `${meta.cache_hits} hits / ${meta.triage_requests} triage calls` : 'Provider history unavailable'}</small></article>
    </div>
    {stats && <div className="split"><article className="panel" aria-label="Counts by category"><h3>By category</h3>
      {Object.entries(stats.data.by_category).map(([name,count]) => <div className="bar-row" key={name}>
        <span>{name}</span><div className="bar-track" aria-hidden="true"><div style={{width:`${Math.min(100, Math.max(0, count / Math.max(1, stats.data.total) * 100))}%`}}/></div><b>{count}</b>
      </div>)}
      {stats.data.total === 0 && <p>No complaints have been recorded yet.</p>}
    </article><article className="panel" aria-label="Counts by priority"><h3>By priority</h3>
      {Object.entries(stats.data.by_priority).map(([name,count]) => <div className="count-row" key={name}><span className={'badge '+name}>{name}</span><b>{count}</b></div>)}
      <p className="muted">Statistics cache TTL: 30 seconds. Writes invalidate cached statistics.</p>
    </article></div>}
    <article className="panel"><h3>Triage provider activity</h3>
      {meta && <><p>Active provider: <strong>{meta.active_provider}</strong></p>
        <p className="muted">Triage result cache TTL: {meta.cache_ttl_seconds} seconds. Most recent outcomes first.</p>
        {meta.recent_outcomes.length === 0 ? <p>No triage activity recorded yet.</p> : <div className="table-scroll"><table>
          <caption className="stats-caption">Latest {meta.recent_outcomes.length} triage outcomes</caption>
          <thead><tr><th scope="col">Provider</th><th scope="col">Latency</th><th scope="col">Fallback</th><th scope="col">Cached result</th><th scope="col">Time</th></tr></thead>
          <tbody>{meta.recent_outcomes.map((row,index) => <tr key={row.timestamp+':'+index}>
            <td>{row.provider}</td><td>{row.latency_ms} ms</td><td>{row.fallback ? 'Yes' : 'No'}</td><td>{row.cache_hit ? 'Yes' : 'No'}</td><td>{new Date(row.timestamp).toLocaleString()}</td>
          </tr>)}</tbody></table></div>}
      </>}
      {!loading && !meta && <p>Provider activity is unavailable. Try Refresh statistics.</p>}
    </article>
  </section>;
}
