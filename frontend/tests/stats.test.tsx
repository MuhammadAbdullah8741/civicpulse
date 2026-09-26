import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError, type ProviderMetadata, type StatsResult } from '../src/api/client';
import { Stats } from '../src/pages/Stats';
const stats: StatsResult = {data:{total:5,by_category:{water:3,roads:2},by_priority:{high:3,normal:2,low:0},by_status:{open:5}},cache:'MISS'};
const meta: ProviderMetadata = {active_provider:'llm:groq',cache_ttl_seconds:86400,triage_requests:4,cache_hits:1,cache_hit_rate:0.25,recent_outcomes:[
  {provider:'rules:fallback',latency_ms:240,cache_hit:false,fallback:true,timestamp:'2026-09-26T00:00:00Z'},
]};
describe('statistics', () => {
  beforeEach(() => {vi.spyOn(api,'stats').mockResolvedValue(stats);vi.spyOn(api,'providers').mockResolvedValue(meta);});
  it('shows actual aggregates, hit rate and provider outcomes', async () => {
    render(<Stats/>);
    expect(await screen.findByText('llm:groq')).toBeInTheDocument();
    expect(within(screen.getByRole('article',{name:'Total reports'})).getByText('5')).toBeInTheDocument();
    expect(within(screen.getByRole('article',{name:'High priority reports'})).getByText('3')).toBeInTheDocument();
    expect(screen.getByText('25.0%')).toBeInTheDocument();
    expect(screen.getByText('rules:fallback')).toBeInTheDocument();
    expect(screen.getByText('240 ms')).toBeInTheDocument();
    const row = screen.getByText('rules:fallback').closest('tr')!;
    expect(within(row).getByText('Yes')).toBeInTheDocument();
    expect(within(row).getByText('No')).toBeInTheDocument();
  });
  it('refreshes MISS to HIT from the API response metadata', async () => {
    vi.mocked(api.stats).mockResolvedValueOnce(stats).mockResolvedValue({...stats,cache:'HIT'});
    render(<Stats/>); expect(await screen.findByText('MISS')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'Refresh statistics'}));
    expect(await screen.findByText('HIT')).toBeInTheDocument();
    expect(api.stats).toHaveBeenCalledTimes(2);
  });
  it('handles zero counts and empty provider history', async () => {
    vi.mocked(api.stats).mockResolvedValue({data:{total:0,by_category:{water:0},by_priority:{high:0},by_status:{open:0}},cache:null});
    vi.mocked(api.providers).mockResolvedValue({...meta,triage_requests:0,cache_hits:0,cache_hit_rate:0,recent_outcomes:[]});
    render(<Stats/>);
    expect(await screen.findByText('No complaints have been recorded yet.')).toBeInTheDocument();
    expect(screen.getByText('No triage activity recorded yet.')).toBeInTheDocument();
    expect(screen.getByText('UNKNOWN')).toBeInTheDocument();
    expect(screen.getByText('0.0%')).toBeInTheDocument();
  });
  it('keeps provider history visible when statistics fail and supports retry', async () => {
    vi.mocked(api.stats).mockRejectedValueOnce(new ApiError('Synthetic stats unavailable',503,null)).mockResolvedValue(stats);
    render(<Stats/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Statistics: Synthetic stats unavailable');
    expect(screen.getByText('llm:groq')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'Refresh statistics'}));
    expect(await screen.findByText('MISS')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
  it('keeps counts visible when provider history fails', async () => {
    vi.mocked(api.providers).mockRejectedValue(new ApiError('Redis unreachable',503,null));
    render(<Stats/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Provider history: Redis unreachable');
    expect(within(screen.getByRole('article',{name:'Total reports'})).getByText('5')).toBeInTheDocument();
  });
  it('shows loading and disables refresh while fetching', async () => {
    let resolve!: (result: StatsResult) => void;
    vi.mocked(api.stats).mockReturnValue(new Promise(r => {resolve=r;}));
    render(<Stats/>);
    expect(screen.getByRole('status')).toHaveTextContent('Loading statistics');
    expect(screen.getByRole('button',{name:'Refresh statistics'})).toBeDisabled();
    await act(async () => {resolve(stats);});
    await waitFor(() => expect(screen.getByRole('button',{name:'Refresh statistics'})).toBeEnabled());
  });
});
