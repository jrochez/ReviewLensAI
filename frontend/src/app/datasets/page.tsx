'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AuthGuard } from '@/components/layout/AuthGuard'
import { TopNav } from '@/components/layout/TopNav'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { Toast } from '@/components/ui/Toast'
import { datasetsApi, scrapeApi } from '@/lib/api'
import { Dataset } from '@/types'
import { Plus, MoreHorizontal, Inbox } from 'lucide-react'

function formatDate(s: string | null) {
  if (!s) return '—'
  try { return new Date(s).toLocaleDateString() } catch { return s }
}

function ActionMenu({ dataset, onDelete, onRescrape }: { dataset: Dataset; onDelete: () => void; onRescrape: () => void }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="relative">
      <button onClick={() => setOpen(o => !o)} className="p-1 hover:bg-raised rounded" aria-label="Actions">
        <MoreHorizontal size={16} className="text-text-secondary" />
      </button>
      {open && (
        <div className="absolute right-0 mt-1 w-36 bg-white border border-border rounded-lg shadow-lg py-1 z-10">
          <Link href={`/datasets/${dataset.id}`} onClick={() => setOpen(false)} className="block px-3 py-2 text-sm text-text-primary hover:bg-raised">View</Link>
          <button onClick={() => { setOpen(false); onRescrape() }} className="w-full text-left px-3 py-2 text-sm text-text-primary hover:bg-raised" disabled={dataset.status === 'scraping'}>Re-scrape</button>
          <div className="border-t border-border my-1" />
          <button onClick={() => { setOpen(false); onDelete() }} className="w-full text-left px-3 py-2 text-sm text-error hover:bg-raised" disabled={dataset.status === 'scraping'}>Delete</button>
        </div>
      )}
    </div>
  )
}

function ConfirmDialog({ name, onConfirm, onCancel }: { name: string; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 max-w-sm w-full mx-4">
        <h2 className="text-base font-semibold mb-2">Delete dataset?</h2>
        <p className="text-sm text-text-secondary mb-6">Deleting <strong>{name}</strong> will permanently remove all reviews and chat history. This cannot be undone.</p>
        <div className="flex gap-3 justify-end">
          <button onClick={onCancel} className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-raised">Cancel</button>
          <button onClick={onConfirm} className="px-4 py-2 text-sm bg-error text-white rounded-lg hover:opacity-90">Delete</button>
        </div>
      </div>
    </div>
  )
}

export default function DatasetsPage() {
  const qc = useQueryClient()
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)
  const [search, setSearch] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<Dataset | null>(null)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsApi.list,
    refetchInterval: (query) => {
      const hasActive = query.state.data?.datasets?.some(d => d.status === 'scraping' || d.status === 'pending')
      return hasActive ? 5000 : 30000
    },
  })

  const { data: rateLimit } = useQuery({
    queryKey: ['rate-limit'],
    queryFn: scrapeApi.rateLimit,
    refetchInterval: 30000,
  })

  const deleteMutation = useMutation({
    mutationFn: datasetsApi.delete,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['datasets'] }); setToast({ msg: 'Dataset deleted.', type: 'success' }) },
    onError: (e: any) => setToast({ msg: e?.data?.message || 'Delete failed.', type: 'error' }),
  })

  const rescrapeMutation = useMutation({
    mutationFn: datasetsApi.rescrape,
    onSuccess: (_, id) => { qc.invalidateQueries({ queryKey: ['datasets'] }); setToast({ msg: 'Scraping started.', type: 'success' }) },
    onError: (e: any) => setToast({ msg: e?.data?.message || 'Re-scrape failed.', type: 'error' }),
  })

  const datasets = data?.datasets ?? []
  const filtered = search ? datasets.filter(d => (d.product_name || d.asin).toLowerCase().includes(search.toLowerCase()) || d.asin.toLowerCase().includes(search.toLowerCase())) : datasets

  return (
    <AuthGuard>
      <div className="flex flex-col min-h-screen">
        <TopNav />
        {toast && <Toast message={toast.msg} type={toast.type} onDismiss={() => setToast(null)} />}
        {deleteTarget && (
          <ConfirmDialog
            name={deleteTarget.product_name || deleteTarget.asin}
            onConfirm={() => { deleteMutation.mutate(deleteTarget.id); setDeleteTarget(null) }}
            onCancel={() => setDeleteTarget(null)}
          />
        )}

        {rateLimit?.suspended && (
          <div className="bg-warning-bg border-b border-warning/20 px-6 py-2 text-sm text-warning" role="alert">
            Scraping is suspended. Daily review limit reached. Scraping resumes at {rateLimit.next_scrape_available_at ? new Date(rateLimit.next_scrape_available_at).toLocaleString() : '—'}.
          </div>
        )}

        <main className="flex-1 px-6 py-6 max-w-6xl mx-auto w-full">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-semibold text-text-primary">Datasets</h1>
            <div className="flex items-center gap-3">
              <input
                type="search"
                placeholder="Search datasets…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-64 px-3 py-1.5 border border-border rounded-lg text-sm bg-raised focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <Link href="/datasets/new" className="inline-flex items-center gap-1.5 bg-accent hover:bg-accent-hover text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
                <Plus size={16} /> New Dataset
              </Link>
            </div>
          </div>

          {isLoading ? (
            <div className="space-y-2">
              {[1,2,3].map(i => <div key={i} className="h-12 bg-raised rounded-lg animate-pulse" />)}
            </div>
          ) : isError ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <p className="text-error text-sm">Failed to load datasets. Please refresh to try again.</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <Inbox size={40} className="text-text-disabled mb-4" />
              <h2 className="text-base font-medium text-text-primary mb-1">No datasets yet</h2>
              <p className="text-sm text-text-secondary mb-4">Add your first Amazon product to get started.</p>
              <Link href="/datasets/new" className="inline-flex items-center gap-1.5 bg-accent text-white text-sm font-medium px-4 py-2 rounded-lg">
                <Plus size={16} /> New Dataset
              </Link>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-text-secondary text-xs font-semibold uppercase tracking-wide">
                  <th className="pb-3 pr-4">Product</th>
                  <th className="pb-3 pr-4">ASIN</th>
                  <th className="pb-3 pr-4">Status</th>
                  <th className="pb-3 pr-4">Reviews</th>
                  <th className="pb-3 pr-4 whitespace-nowrap">Updated</th>
                  <th className="pb-3" />
                </tr>
              </thead>
              <tbody>
                {filtered.map(ds => (
                  <tr key={ds.id} className="border-b border-border hover:bg-raised/50 transition-colors">
                    <td className="py-3 pr-4 font-medium text-text-primary">
                      <Link href={`/datasets/${ds.id}`} className="hover:text-accent">{ds.product_name || ds.asin}</Link>
                    </td>
                    <td className="py-3 pr-4 font-mono text-xs text-text-secondary">{ds.asin}</td>
                    <td className="py-3 pr-4"><StatusBadge status={ds.status} /></td>
                    <td className="py-3 pr-4 text-text-secondary">{ds.review_count ?? '—'}</td>
                    <td className="py-3 pr-4 text-text-secondary whitespace-nowrap">{formatDate(ds.last_scraped_at || ds.created_at)}</td>
                    <td className="py-3">
                      <ActionMenu dataset={ds} onDelete={() => setDeleteTarget(ds)} onRescrape={() => rescrapeMutation.mutate(ds.id)} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </main>
      </div>
    </AuthGuard>
  )
}
