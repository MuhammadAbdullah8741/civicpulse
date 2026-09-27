import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError, type Complaint, type ComplaintPage } from '../src/api/client';
import { Dashboard } from '../src/pages/Dashboard';

const item: Complaint = {
  id: '11111111-1111-4111-8111-111111111111', text: 'Burst pipe flooding the street.',
  location: 'Synthetic Street', reporter_contact: null, category: 'water', priority: 'high',
  status: 'open', ai_summary: 'Burst pipe flooding the street.', triaged_by: 'simulated',
  triage_latency_ms: 3, created_at: '2026-09-26T00:00:00Z', updated_at: '2026-09-26T00:00:00Z',
  allowed_transitions: ['in_progress', 'rejected'],
};
const page: ComplaintPage = {items:[item], total:1, page:1, page_size:10};
async function ready() {
  await waitFor(() => expect(screen.queryByText('Loading reports…')).not.toBeInTheDocument());
}
describe('operations dashboard', () => {
  beforeEach(() => {
    vi.spyOn(api, 'list').mockResolvedValue(page);
    vi.spyOn(api, 'update').mockResolvedValue({...item, status:'in_progress', allowed_transitions:['resolved','rejected']});
  });
  it('shows loading while fetching and then displays a report', async () => {
    let resolve!: (value: ComplaintPage) => void;
    vi.mocked(api.list).mockReturnValue(new Promise(r => {resolve = r;}));
    render(<Dashboard/>);
    expect(screen.getByText('Loading reports…')).toBeInTheDocument();
    await act(async () => {resolve(page);});
    expect(screen.getByRole('heading', {name:item.ai_summary!})).toBeInTheDocument();
    expect(api.list).toHaveBeenCalledWith({page:1, page_size:10});
  });
  it('displays the empty state', async () => {
    vi.mocked(api.list).mockResolvedValue({...page, items:[], total:0});
    render(<Dashboard/>);
    expect(await screen.findByText('No reports match these filters.')).toBeInTheDocument();
    expect(screen.getByRole('button', {name:'Next'})).toBeDisabled();
  });
  it('shows a load failure and supports retry', async () => {
    vi.mocked(api.list).mockRejectedValueOnce(new Error('Synthetic unavailable')).mockResolvedValue(page);
    render(<Dashboard/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Synthetic unavailable');
    await ready();
    fireEvent.click(screen.getByRole('button', {name:'Refresh reports'}));
    expect(await screen.findByRole('heading', {name:item.ai_summary!})).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
  it('paginates and resets to page one when filters change', async () => {
    vi.mocked(api.list).mockImplementation(async filters => ({...page, total:21, page:filters?.page ?? 1}));
    render(<Dashboard/>); await ready();
    fireEvent.click(screen.getByRole('button', {name:'Next'}));
    await waitFor(() => expect(api.list).toHaveBeenLastCalledWith({page:2,page_size:10}));
    await ready();
    fireEvent.change(screen.getByLabelText('Category'), {target:{value:'water'}});
    await waitFor(() => expect(api.list).toHaveBeenLastCalledWith({page:1,page_size:10,category:'water'}));
    await ready();
    fireEvent.change(screen.getByLabelText('Priority'), {target:{value:'high'}});
    await waitFor(() => expect(api.list).toHaveBeenLastCalledWith(expect.objectContaining({priority:'high',page:1})));
    await ready();
    fireEvent.change(screen.getByLabelText('Status'), {target:{value:'open'}});
    await waitFor(() => expect(api.list).toHaveBeenLastCalledWith({page:1,page_size:10,category:'water',priority:'high',status:'open'}));
  });
  it('disables pagination at the first and last pages', async () => {
    render(<Dashboard/>); await ready();
    expect(screen.getByRole('button', {name:'Previous'})).toBeDisabled();
    expect(screen.getByRole('button', {name:'Next'})).toBeDisabled();
  });
  it('renders only transitions provided by the backend and no terminal actions', async () => {
    const terminal: Complaint = {...item,id:'22222222-2222-4222-8222-222222222222',status:'resolved',allowed_transitions:[]};
    vi.mocked(api.list).mockResolvedValue({...page,items:[item,terminal],total:2});
    render(<Dashboard/>); await ready();
    const open = within(screen.getByRole('article', {name:'Report '+item.id}));
    expect(open.getByRole('button', {name:'Set in progress'})).toBeInTheDocument();
    expect(open.queryByRole('button', {name:'Set resolved'})).not.toBeInTheDocument();
    const closed = within(screen.getByRole('article', {name:'Report '+terminal.id}));
    expect(closed.queryByRole('button')).not.toBeInTheDocument();
    expect(closed.getByText('No further actions')).toBeInTheDocument();
  });
  it('updates status through the API and reloads the queue', async () => {
    vi.mocked(api.list).mockResolvedValueOnce(page).mockResolvedValue({...page,items:[{...item,status:'in_progress',allowed_transitions:['resolved','rejected']}]});
    render(<Dashboard/>); await ready();
    fireEvent.click(screen.getByRole('button', {name:'Set in progress'}));
    expect(await screen.findByText('Status updated.')).toBeInTheDocument();
    await ready();
    expect(api.update).toHaveBeenCalledWith(item.id,'in_progress');
    expect(screen.getByRole('button', {name:'Set resolved'})).toBeInTheDocument();
  });
  it('displays the exact server 409 message and keeps the record unchanged', async () => {
    const detail = 'Invalid status transition: resolved -> in_progress';
    vi.mocked(api.update).mockRejectedValue(new ApiError(detail,409,null));
    render(<Dashboard/>); await ready();
    fireEvent.click(screen.getByRole('button', {name:'Set in progress'}));
    expect(await screen.findByRole('alert')).toHaveTextContent(detail);
    expect(screen.getByRole('button', {name:'Set in progress'})).toBeEnabled();
    expect(api.list).toHaveBeenCalledTimes(1);
  });
});
