import { useEffect, useRef, useState } from 'react';
import { api, type Category, type ComplaintPage, type Filters, type Priority, type Status } from '../api/client';
import './dashboard.css';

const categories: Category[] = ['water', 'electricity', 'sanitation', 'roads', 'streetlights', 'other'];
const priorities: Priority[] = ['high', 'normal', 'low'];
const statuses: Status[] = ['open', 'in_progress', 'resolved', 'rejected'];
const label = (value: string) => value.replaceAll('_', ' ');
const message = (error: unknown) => error instanceof Error ? error.message : 'Unable to load reports. Please retry.';

export function Dashboard() {
  const [filters, setFilters] = useState<Filters>({page: 1, page_size: 10});
  const [revision, setRevision] = useState(0);
  const [data, setData] = useState<ComplaintPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [actionError, setActionError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState('');
  const mutation = useRef(false);
  const mounted = useRef(false);

  useEffect(() => { mounted.current = true; return () => {mounted.current = false;}; }, []);
  useEffect(() => {
    let active = true;
    setLoading(true); setLoadError('');
    api.list(filters).then(result => {
      if (!active) return;
      const lastPage = Math.max(1, Math.ceil(result.total / result.page_size));
      if (result.page > lastPage) {
        setFilters(previous => ({...previous, page: lastPage}));
      } else {setData(result);}
    }).catch(error => {if (active) setLoadError(message(error));})
      .finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [filters, revision]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (!document.hidden && !mutation.current) setRevision(value => value + 1);
    }, 15000);
    return () => window.clearInterval(timer);
  }, []);

  function filter(key: 'category' | 'priority' | 'status', value: string) {
    setActionError(''); setNotice('');
    setFilters(previous => ({...previous, [key]: value || undefined, page: 1}));
  }
  async function update(id: string, next: Status) {
    if (mutation.current) return;
    mutation.current = true; setBusy(id); setActionError(''); setNotice('');
    try {
      await api.update(id, next);
      if (mounted.current) {setNotice('Status updated.'); setRevision(value => value + 1);}
    } catch (error) {
      if (mounted.current) setActionError(message(error));
    } finally {
      mutation.current = false;
      if (mounted.current) setBusy('');
    }
  }

  return <section className="panel" aria-labelledby="dashboard-title">
    <div className="section-head"><div><span className="eyebrow">OPERATIONS</span>
      <h2 id="dashboard-title">The neighbourhood queue</h2>
      <p className="muted">Refreshes every 15 seconds while this tab is visible.</p></div>
      <button className="secondary" disabled={loading || Boolean(busy)} onClick={() => setRevision(value => value + 1)}>Refresh reports</button>
    </div>
    <fieldset className="dashboard-filters" disabled={Boolean(busy)}><legend>Filter reports</legend>
      <label>Category<select value={filters.category || ''} onChange={e => filter('category', e.target.value)}>
        <option value="">All categories</option>{categories.map(value => <option key={value} value={value}>{label(value)}</option>)}
      </select></label>
      <label>Priority<select value={filters.priority || ''} onChange={e => filter('priority', e.target.value)}>
        <option value="">All priorities</option>{priorities.map(value => <option key={value} value={value}>{label(value)}</option>)}
      </select></label>
      <label>Status<select value={filters.status || ''} onChange={e => filter('status', e.target.value)}>
        <option value="">All statuses</option>{statuses.map(value => <option key={value} value={value}>{label(value)}</option>)}
      </select></label>
    </fieldset>
    {loadError && <p role="alert" className="error">{loadError}</p>}
    {actionError && <p role="alert" className="error">{actionError}</p>}
    {notice && <p role="status">{notice}</p>}
    {loading && <p role="status">Loading reports…</p>}
    {!loading && !loadError && data?.items.length === 0 && <p className="empty">No reports match these filters.</p>}
    {!loadError && <div className="reports" aria-busy={loading}>
      {data?.items.map(item => <article className="report" key={item.id} aria-label={'Report ' + item.id}>
        <div className="report-body"><div className="tags"><span className={'badge ' + item.priority}>{item.priority}</span>
          <span className="badge">{item.category}</span><span className="muted">{label(item.status)}</span></div>
          <h3>{item.ai_summary || item.text}</h3><p>{item.location} · {new Date(item.created_at).toLocaleString()}</p>
          <details><summary>Report details</summary><p>{item.text}</p>
            <small>Provider: {item.triaged_by} · {item.triage_latency_ms} ms · Reference: {item.id}</small>
          </details>
        </div>
        <div className="actions">{item.allowed_transitions.map(next =>
          <button className="secondary" key={next} disabled={loading || Boolean(busy)}
            onClick={() => void update(item.id, next)}>Set {label(next)}</button>)}
          {item.allowed_transitions.length === 0 && <span className="muted">No further actions</span>}
          {busy === item.id && <span role="status">Saving status…</span>}
        </div>
      </article>)}
    </div>}
    <div className="pagination"><span>{data?.total ?? 0} reports · Page {filters.page ?? 1} of {Math.max(1, Math.ceil((data?.total ?? 0) / (filters.page_size ?? 10)))}</span>
      <div><button className="secondary" disabled={loading || Boolean(busy) || (filters.page ?? 1) <= 1}
        onClick={() => setFilters(previous => ({...previous, page: (previous.page ?? 1) - 1}))}>Previous</button>
      <button className="secondary" disabled={loading || Boolean(busy) || Boolean(loadError) || !data || (filters.page ?? 1) * (filters.page_size ?? 10) >= data.total}
        onClick={() => setFilters(previous => ({...previous, page: (previous.page ?? 1) + 1}))}>Next</button></div>
    </div>
  </section>;
}
