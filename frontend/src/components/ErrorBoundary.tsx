import { Component, type ReactNode } from 'react';

export class ErrorBoundary extends Component<{children: ReactNode}, {failed: boolean}> {
  state = {failed: false};
  static getDerivedStateFromError() { return {failed: true}; }
  render() {
    if (this.state.failed) return <section className="panel" role="alert">
      <h2>Something went wrong</h2>
      <p>Reload the page; reports already saved remain available.</p>
      <button onClick={() => window.location.reload()}>Reload application</button>
    </section>;
    return this.props.children;
  }
}
