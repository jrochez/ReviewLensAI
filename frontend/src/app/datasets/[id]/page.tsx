'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { AuthGuard } from '@/components/layout/AuthGuard'
import { TopNav } from '@/components/layout/TopNav'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { StarRating } from '@/components/ui/StarRating'
import { datasetsApi, reviewsApi } from '@/lib/api'
import { Review } from '@/types'
import { ArrowLeft, MessageSquare, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'

function SentimentBar({ label, count, pct, color }: { label: string; count: number; pct: number; color: string }) {
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-20 text-text-secondary capitalize">{label}</span>
      <div className="flex-1 bg-raised rounded-full h-2 overflow-hidden">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-16 text-right text-text-secondary">{pct}% ({count})</span>
    </div>
  )
}

function ReviewRow({ review }: { review: Review }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <>
      <tr className="border-b border-border hover:bg-raised/50 cursor-pointer transition-colors" onClick={() => setExpanded(e => !e)}>
        <td className="py-2.5 pr-4"><StarRating rating={review.star_rating} /></td>
        <td className="py-2.5 pr-4 text-xs text-text-secondary">{review.review_date || '—'}</td>
        <td className="py-2.5 pr-4 text-xs">{review.reviewer_name || '—'}</td>
        <td className="py-2.5 pr-4 text-center text-xs">{review.verified_purchase ? '✓' : '—'}</td>
        <td className="py-2.5 pr-2 text-xs text-text-secondary max-w-xs truncate">{review.review_text.slice(0, 80)}…</td>
        <td className="py-2.5 text-text-disabled">{expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</td>
      </tr>
      {expanded && (
        <tr className="bg-accent-subtle">
          <td colSpan={6} className="px-4 py-3 text-sm text-text-primary">{review.review_text}</td>
        </tr>
      )}
    </>
  )
}

export default function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState('date_desc')
  const [starsFilter, setStarsFilter] = useState<number[]>([])

  const { data: ds, isLoading: dsLoading, isError: dsError } = useQuery({
    queryKey: ['dataset', id],
    queryFn: () => datasetsApi.get(id),
    refetchInterval: (query) => (query.state.data?.status === 'scraping' || query.state.data?.status === 'pending') ? 5000 : false,
  })

  const { data: summary } = useQuery({
    queryKey: ['summary', id],
    queryFn: () => reviewsApi.summary(id),
    enabled: ds?.status === 'ready',
  })

  const { data: reviewsData } = useQuery({
    queryKey: ['reviews', id, page, sort, starsFilter],
    queryFn: () => reviewsApi.list(id, {
      page,
      per_page: 25,
      sort,
      ...(starsFilter.length ? { stars: starsFilter.join(',') } : {}),
    }),
    enabled: ds?.status === 'ready',
  })

  if (dsLoading) return (
    <AuthGuard>
      <div className="flex flex-col min-h-screen"><TopNav />
        <div className="flex-1 flex items-center justify-center text-text-secondary">Loading…</div>
      </div>
    </AuthGuard>
  )

  if (dsError) return (
    <AuthGuard>
      <div className="flex flex-col min-h-screen"><TopNav />
        <div className="flex-1 flex items-center justify-center text-error text-sm">Failed to load dataset. Please go back and try again.</div>
      </div>
    </AuthGuard>
  )

  if (!ds) return (
    <AuthGuard>
      <div className="flex flex-col min-h-screen"><TopNav />
        <div className="flex-1 flex items-center justify-center text-text-secondary">Dataset not found.</div>
      </div>
    </AuthGuard>
  )

  return (
    <AuthGuard>
      <div className="flex flex-col min-h-screen">
        <TopNav />
        <main className="flex-1 px-6 py-6 max-w-6xl mx-auto w-full">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <div className="flex items-center gap-2 text-text-secondary text-sm mb-1">
                <Link href="/datasets" className="hover:text-text-primary flex items-center gap-1"><ArrowLeft size={14} /> Datasets</Link>
              </div>
              <h1 className="text-2xl font-semibold text-text-primary">{ds.product_name || ds.asin}</h1>
              <div className="flex items-center gap-3 mt-1">
                <span className="font-mono text-xs text-text-secondary">ASIN: {ds.asin}</span>
                <StatusBadge status={ds.status} />
                {ds.last_scraped_at && <span className="text-xs text-text-secondary">Last scraped {new Date(ds.last_scraped_at).toLocaleDateString()}</span>}
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => datasetsApi.rescrape(id)} className="flex items-center gap-1.5 px-4 py-2 text-sm border border-border rounded-lg hover:bg-raised transition-colors">
                <RefreshCw size={14} /> Re-scrape
              </button>
              <Link href={`/datasets/${id}/chat`} className="flex items-center gap-1.5 px-4 py-2 text-sm bg-accent hover:bg-accent-hover text-white rounded-lg transition-colors font-medium">
                <MessageSquare size={14} /> Ask Questions
              </Link>
            </div>
          </div>

          {ds.status !== 'ready' && (
            <div className="text-center py-16 text-text-secondary">
              {ds.status === 'error' ? <p className="text-error">{ds.error_message || 'Scraping failed.'}</p> : <p>Dataset is {ds.status}. Please wait…</p>}
            </div>
          )}

          {ds.status === 'ready' && summary && (
            <>
              {/* 2-col grid: stats + sentiment */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                <div className="bg-white border border-border rounded-xl p-5">
                  <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">Review Stats</h2>
                  <div className="space-y-1.5 text-sm">
                    <div className="flex justify-between"><span className="text-text-secondary">Total reviews</span><span className="font-semibold">{summary.stats.review_count.toLocaleString()}</span></div>
                    <div className="flex justify-between items-center"><span className="text-text-secondary">Avg rating</span><div className="flex items-center gap-1"><StarRating rating={summary.stats.avg_star_rating || 0} /><span className="text-xs text-text-secondary">{summary.stats.avg_star_rating?.toFixed(1)}</span></div></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Date range</span><span>{summary.stats.review_date_min} – {summary.stats.review_date_max}</span></div>
                    <div className="flex justify-between"><span className="text-text-secondary">Verified</span><span>{summary.stats.verified_count} ({Math.round(summary.stats.verified_count / summary.stats.review_count * 100)}%)</span></div>
                  </div>
                </div>
                <div className="bg-white border border-border rounded-xl p-5">
                  <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">Sentiment</h2>
                  <div className="space-y-3">
                    <SentimentBar label="positive" count={summary.sentiment.positive.count} pct={summary.sentiment.positive.pct} color="bg-success" />
                    <SentimentBar label="neutral" count={summary.sentiment.neutral.count} pct={summary.sentiment.neutral.pct} color="bg-neutral" />
                    <SentimentBar label="negative" count={summary.sentiment.negative.count} pct={summary.sentiment.negative.pct} color="bg-error" />
                  </div>
                </div>
              </div>

              {/* 2-col grid: themes + filter hint */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                <div className="bg-white border border-border rounded-xl p-5">
                  <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">Top Themes</h2>
                  {summary.themes.length === 0 ? (
                    <p className="text-sm text-text-secondary">Not enough theme data.</p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {summary.themes.slice(0, 20).map(t => (
                        <span key={t.theme} className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-raised rounded-full text-xs">
                          <span className="font-medium text-text-primary">{t.theme}</span>
                          <span className="text-text-secondary">{t.frequency}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="bg-white border border-border rounded-xl p-5">
                  <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">Filter Reviews</h2>
                  <div className="flex flex-wrap gap-2">
                    {[5,4,3,2,1].map(star => (
                      <button
                        key={star}
                        onClick={() => setStarsFilter(prev => prev.includes(star) ? prev.filter(s => s !== star) : [...prev, star])}
                        className={`flex items-center gap-1 px-2.5 py-1 rounded-full border text-xs transition-colors ${starsFilter.includes(star) ? 'bg-accent text-white border-accent' : 'bg-white border-border text-text-secondary hover:bg-raised'}`}
                      >
                        {star}★
                      </button>
                    ))}
                  </div>
                  <div className="mt-3">
                    <select value={sort} onChange={e => setSort(e.target.value)} className="w-full text-xs border border-border rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-accent">
                      <option value="date_desc">Newest first</option>
                      <option value="date_asc">Oldest first</option>
                      <option value="stars_desc">Highest rated</option>
                      <option value="stars_asc">Lowest rated</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Review table */}
              <div className="bg-white border border-border rounded-xl overflow-hidden">
                <div className="px-5 py-4 border-b border-border">
                  <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide">Reviews ({reviewsData?.total ?? 0})</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-xs font-semibold text-text-secondary uppercase tracking-wide">
                        <th className="px-5 py-3 text-left">Rating</th>
                        <th className="px-4 py-3 text-left">Date</th>
                        <th className="px-4 py-3 text-left">Reviewer</th>
                        <th className="px-4 py-3 text-center">Verified</th>
                        <th className="px-4 py-3 text-left">Review</th>
                        <th className="px-4 py-3" />
                      </tr>
                    </thead>
                    <tbody>
                      {reviewsData?.reviews.map(r => <ReviewRow key={r.id} review={r} />)}
                    </tbody>
                  </table>
                </div>
                {reviewsData && reviewsData.total > reviewsData.per_page && (
                  <div className="flex items-center justify-between px-5 py-3 border-t border-border text-sm">
                    <span className="text-text-secondary">Page {page} of {Math.ceil(reviewsData.total / reviewsData.per_page)}</span>
                    <div className="flex gap-2">
                      <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 border border-border rounded hover:bg-raised disabled:opacity-40">Prev</button>
                      <button disabled={page >= Math.ceil(reviewsData.total / reviewsData.per_page)} onClick={() => setPage(p => p + 1)} className="px-3 py-1 border border-border rounded hover:bg-raised disabled:opacity-40">Next</button>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </main>
      </div>
    </AuthGuard>
  )
}
