import { useState } from 'react';

const views = {
  Dashboard: {title: 'The neighbourhood queue', description: 'Complaint filters, pagination and status actions will be added in the dashboard phase.'},
  'Submit report': {title: 'Report a local issue', description: 'The citizen submission form will be added in the next phase.'},
  Statistics: {title: 'Your city at a glance', description: 'Live category counts and cache visibility will be connected in the statistics phase.'},
};
type View = keyof typeof views;
export default function App() {
  const [page, setPage] = useState<View>('Dashboard');
  return <>
    <header><a className="brand" href="#" onClick={event => {event.preventDefault();setPage('Dashboard');}}>
      <span className="brand-icon" aria-hidden="true">C</span>CivicPulse
      <span className="brand-sub">NEIGHBOURHOOD OPERATIONS</span>
    </a><span className="demo-label">Development preview</span></header>
    <main>
      <div className="intro"><span className="eyebrow">LOCAL ISSUES. SHARED PROGRESS.</span>
        <h1>A pulse on your neighbourhood.</h1>
        <p>Report what matters. Prioritise what’s urgent. Follow every resolution.</p>
      </div>
      <nav aria-label="Main navigation">{(Object.keys(views) as View[]).map(label =>
        <button key={label} aria-current={page === label ? 'page' : undefined}
          className={page === label ? 'active' : ''} onClick={() => setPage(label)}>{label}</button>
      )}</nav>
      <section className="panel" aria-labelledby="view-title">
        <span className="eyebrow">FRONTEND FOUNDATION</span>
        <h2 id="view-title">{views[page].title}</h2>
        <p className="muted">{views[page].description}</p>
      </section>
    </main>
    <footer>CivicPulse · Built for clearer municipal response.<span>Foundation phase · Use synthetic test data</span></footer>
  </>;
}
