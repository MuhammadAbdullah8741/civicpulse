import { useState } from 'react';
import { Submit } from './pages/Submit';
import { Dashboard } from './pages/Dashboard';
import { Stats } from './pages/Stats';

const views = {
  Dashboard: true,
  'Submit report': true,
  Statistics: true,
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
      {page === 'Submit report' ? <Submit/> : page === 'Dashboard' ? <Dashboard/> : <Stats/>}
    </main>
    <footer>CivicPulse · Built for clearer municipal response.<span>Use synthetic test data</span></footer>
  </>;
}
