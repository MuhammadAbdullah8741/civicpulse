import { useRef, useState, type FormEvent } from 'react';
import { api, ApiError, type Complaint } from '../api/client';
import './submit.css';

type Errors = Partial<Record<'text' | 'location' | 'reporter_contact', string>>;
const length = (value: string) => Array.from(value).length;

export function Submit() {
  const [text, setText] = useState('');
  const [location, setLocation] = useState('');
  const [contact, setContact] = useState('');
  const [errors, setErrors] = useState<Errors>({});
  const [message, setMessage] = useState('');
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<Complaint | null>(null);
  const inFlight = useRef(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current || result) return;
    const body = {text: text.trim(), location: location.trim(), reporter_contact: contact.trim() || null};
    const invalid: Errors = {};
    if (length(body.text) < 10 || length(body.text) > 2000) invalid.text = 'Enter a description between 10 and 2000 characters.';
    if (length(body.location) < 3 || length(body.location) > 200) invalid.location = 'Enter a location between 3 and 200 characters.';
    setErrors(invalid); setMessage('');
    if (Object.keys(invalid).length) return;
    inFlight.current = true; setPending(true);
    try {
      setResult(await api.create(body));
    } catch (error) {
      if (error instanceof ApiError) {
        const serverFields: Errors = {};
        for (const item of error.fields) {
          const key = item.field.replace(/^body\./, '');
          if (key === 'text' || key === 'location' || key === 'reporter_contact') serverFields[key] = item.message;
        }
        setErrors(serverFields);
        setMessage(error.status === 429
          ? `${error.message} Retry after ${error.retryAfter || '60'} seconds.`
          : error.message);
      } else {
        setMessage('Unable to confirm submission. Check your connection. The report may have been saved; check the dashboard before retrying.');
      }
    } finally {
      inFlight.current = false; setPending(false);
    }
  }

  function reset() {
    setResult(null); setText(''); setLocation(''); setContact(''); setErrors({}); setMessage('');
  }

  return <div className="split">
    <section className="panel" aria-labelledby="submit-title">
      <span className="eyebrow">CITIZEN REPORT</span>
      <h2 id="submit-title">Report a local issue</h2>
      <p className="muted">Describe the problem. The backend assigns its category and priority.</p>
      {result ? <div role="status" className="submission-success">
        <h3>Report received</h3>
        <dl><dt>Category</dt><dd>{result.category}</dd><dt>Priority</dt><dd>{result.priority}</dd>
          <dt>Summary</dt><dd>{result.ai_summary || 'No summary provided.'}</dd>
          <dt>Provider</dt><dd>{result.triaged_by}</dd>
          <dt>Triage time</dt><dd>{result.triage_latency_ms} ms</dd>
          <dt>Reference</dt><dd>{result.id}</dd></dl>
        <button onClick={reset}>Submit another report</button>
      </div> : <form onSubmit={submit} noValidate aria-busy={pending}>
        <fieldset disabled={pending} className="submission-fields">
          <label htmlFor="complaint-text">Description</label>
          <textarea id="complaint-text" rows={6} value={text} onChange={e => setText(e.target.value)}
            aria-invalid={Boolean(errors.text)} aria-describedby="text-help text-error" required/>
          <small id="text-help">10–2000 characters · {length(text.trim())} entered</small>
          <p id="text-error" className="field-error">{errors.text}</p>
          <label htmlFor="complaint-location">Location</label>
          <input id="complaint-location" value={location} onChange={e => setLocation(e.target.value)}
            aria-invalid={Boolean(errors.location)} aria-describedby="location-help location-error" required/>
          <small id="location-help">3–200 characters · street, sector or landmark</small>
          <p id="location-error" className="field-error">{errors.location}</p>
          <label htmlFor="complaint-contact">Contact (optional)</label>
          <input id="complaint-contact" value={contact} onChange={e => setContact(e.target.value)}
            aria-invalid={Boolean(errors.reporter_contact)} aria-describedby="contact-error"/>
          <p id="contact-error" className="field-error">{errors.reporter_contact}</p>
          <p className="privacy">Use synthetic details for this demonstration. Avoid personal information in the description.</p>
          <button type="submit">{pending ? 'Analysing and saving…' : 'Submit report'}</button>
        </fieldset>
        {pending && <p role="status">Triage is in progress. A provider retry can take more than 20 seconds.</p>}
        {message && <p role="alert" className="error">{message}</p>}
      </form>}
    </section>
    <aside className="panel dark"><span className="eyebrow">HOW IT WORKS</span>
      <h2>One report.<br/>A clearer response.</h2>
      <ol><li>Describe the issue in your own words.</li><li>Triage assigns a category and priority.</li><li>Your report is saved for operator review.</li></ol>
      <p>This demonstration is not an emergency response service.</p>
    </aside>
  </div>;
}
