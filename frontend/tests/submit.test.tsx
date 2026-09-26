import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError, type Complaint } from '../src/api/client';
import { Submit } from '../src/pages/Submit';

const saved: Complaint = {
  id: '123e4567-e89b-42d3-a456-426614174000', text: 'Burst water pipe flooding the street.',
  location: 'Synthetic Street', reporter_contact: null, category: 'water', priority: 'high',
  status: 'open', ai_summary: 'Burst pipe flooding the street.', triaged_by: 'simulated',
  triage_latency_ms: 12, created_at: '2026-09-26T00:00:00Z', updated_at: '2026-09-26T00:00:00Z',
  allowed_transitions: ['in_progress', 'rejected'],
};
function fill(text = '  Burst water pipe flooding the street.  ', location = '  Synthetic Street  ') {
  fireEvent.change(screen.getByLabelText('Description'), {target: {value: text}});
  fireEvent.change(screen.getByLabelText('Location'), {target: {value: location}});
}
describe('complaint submission', () => {
  beforeEach(() => {vi.spyOn(api, 'create').mockResolvedValue(saved);});
  it('rejects short trimmed fields without an API call', () => {
    render(<Submit/>); fill(' short ', ' ab ');
    fireEvent.click(screen.getByRole('button', {name: 'Submit report'}));
    expect(screen.getByLabelText('Description')).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByLabelText('Location')).toHaveAttribute('aria-invalid', 'true');
    expect(api.create).not.toHaveBeenCalled();
  });
  it('rejects fields above server length limits', () => {
    render(<Submit/>); fill('x'.repeat(2001), 'x'.repeat(201));
    fireEvent.click(screen.getByRole('button', {name: 'Submit report'}));
    expect(screen.getByText('Enter a description between 10 and 2000 characters.')).toBeInTheDocument();
    expect(screen.getByText('Enter a location between 3 and 200 characters.')).toBeInTheDocument();
    expect(api.create).not.toHaveBeenCalled();
  });
  it('trims input, sends null contact, displays server triage, and permits a new report', async () => {
    render(<Submit/>); fill();
    fireEvent.click(screen.getByRole('button', {name: 'Submit report'}));
    expect(await screen.findByRole('heading', {name: 'Report received'})).toBeInTheDocument();
    expect(api.create).toHaveBeenCalledWith({text: saved.text, location: saved.location, reporter_contact: null});
    for (const value of ['water', 'high', saved.ai_summary!, 'simulated', saved.id, '12 ms']) expect(screen.getByText(value)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', {name: 'Submit another report'}));
    expect(screen.getByLabelText('Description')).toHaveValue('');
  });
  it('disables submission while pending and sends optional contact', async () => {
    let resolve!: (value: Complaint) => void;
    vi.mocked(api.create).mockReturnValue(new Promise<Complaint>(r => {resolve = r;}));
    render(<Submit/>); fill();
    fireEvent.change(screen.getByLabelText('Contact (optional)'), {target: {value: ' synthetic@example.com '}});
    fireEvent.click(screen.getByRole('button', {name: 'Submit report'}));
    const button = screen.getByRole('button', {name: 'Analysing and saving…'});
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(api.create).toHaveBeenCalledTimes(1);
    expect(api.create).toHaveBeenCalledWith(expect.objectContaining({reporter_contact: 'synthetic@example.com'}));
    await act(async () => {resolve(saved);});
    expect(screen.getByRole('heading', {name: 'Report received'})).toBeInTheDocument();
  });
  it('renders server field validation errors', async () => {
    vi.mocked(api.create).mockRejectedValue(new ApiError('Validation failed', 400, null, [{field:'body.location', message:'Synthetic server field error'}]));
    render(<Submit/>); fill(); fireEvent.click(screen.getByRole('button', {name:'Submit report'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('Validation failed');
    expect(screen.getByText('Synthetic server field error')).toBeInTheDocument();
    expect(screen.getByLabelText('Location')).toHaveAttribute('aria-invalid','true');
  });
  it('shows Retry-After for rate-limited submissions', async () => {
    vi.mocked(api.create).mockRejectedValue(new ApiError('Too many complaints.', 429, '23'));
    render(<Submit/>); fill(); fireEvent.click(screen.getByRole('button', {name:'Submit report'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('Retry after 23 seconds.');
    expect(screen.getByRole('button', {name:'Submit report'})).toBeEnabled();
  });
  it('preserves input after a network failure and warns about uncertain persistence', async () => {
    vi.mocked(api.create).mockRejectedValue(new TypeError('Failed to fetch'));
    render(<Submit/>); fill(); fireEvent.click(screen.getByRole('button', {name:'Submit report'}));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('The report may have been saved'));
    expect(screen.getByLabelText('Description')).toHaveValue('  Burst water pipe flooding the street.  ');
  });
});
