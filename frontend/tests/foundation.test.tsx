import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../src/App';
import { api } from '../src/api/client';
import { ErrorBoundary } from '../src/components/ErrorBoundary';

describe('frontend foundation', () => {
  beforeEach(() => {vi.spyOn(api, 'list').mockResolvedValue({items:[],total:0,page:1,page_size:10});});
  it('opens the dashboard with accessible navigation', async () => {
    render(<App/>);
    await screen.findByText('No reports match these filters.');
    expect(screen.getByRole('navigation', {name: 'Main navigation'})).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: 'The neighbourhood queue'})).toBeInTheDocument();
    expect(screen.getByRole('button', {name: 'Dashboard'})).toHaveAttribute('aria-current', 'page');
  });
  it('navigates to the submission view', async () => {
    const user = userEvent.setup(); render(<App/>);
    await user.click(screen.getByRole('button', {name: 'Submit report'}));
    expect(screen.getByRole('heading', {name: 'Report a local issue'})).toBeInTheDocument();
    expect(screen.getByRole('button', {name: 'Dashboard'})).not.toHaveAttribute('aria-current');
  });
  it('navigates to the statistics view', async () => {
    const user = userEvent.setup(); render(<App/>);
    await user.click(screen.getByRole('button', {name: 'Statistics'}));
    expect(screen.getByRole('heading', {name: 'Your city at a glance'})).toBeInTheDocument();
  });
  it('returns home through the brand link', async () => {
    const user = userEvent.setup(); render(<App/>);
    await user.click(screen.getByRole('button', {name: 'Statistics'}));
    await user.click(screen.getByRole('link', {name: /CivicPulse/}));
    expect(screen.getByRole('heading', {name: 'The neighbourhood queue'})).toBeInTheDocument();
  });
  it('contains a render failure with recovery instructions', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    function Broken(): never { throw new Error('Synthetic render failure'); }
    render(<ErrorBoundary><Broken/></ErrorBoundary>);
    expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong');
    expect(screen.getByRole('button', {name: 'Reload application'})).toBeInTheDocument();
  });
});
