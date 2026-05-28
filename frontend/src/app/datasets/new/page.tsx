'use client'

import { useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { AuthGuard } from '@/components/layout/AuthGuard'
import { TopNav } from '@/components/layout/TopNav'
import { datasetsApi } from '@/lib/api'
import { ArrowLeft, CheckCircle2, Circle, Loader2, Upload } from 'lucide-react'

type Step = { label: string; status: 'pending' | 'active' | 'done' | 'error' }
type Tab = 'asin' | 'csv' | 'json'

export default function NewDatasetPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<Tab>('asin')

  // ASIN/URL flow
  const [input, setInput] = useState('')
  const [inputError, setInputError] = useState('')
  const [loading, setLoading] = useState(false)
  const [steps, setSteps] = useState<Step[]>([
    { label: 'Submitting dataset', status: 'pending' },
    { label: 'Collecting reviews (Bright Data)', status: 'pending' },
    { label: 'Processing & indexing', status: 'pending' },
    { label: 'Finalizing', status: 'pending' },
  ])
  const [globalError, setGlobalError] = useState('')

  // Upload flow
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const csvRef = useRef<HTMLInputElement>(null)
  const jsonRef = useRef<HTMLInputElement>(null)
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [jsonFile, setJsonFile] = useState<File | null>(null)

  const updateStep = (i: number, status: Step['status']) => {
    setSteps(prev => prev.map((s, idx) => idx === i ? { ...s, status } : s))
  }

  const pollStatus = async (id: string) => {
    updateStep(0, 'done')
    updateStep(1, 'active')
    let ticks = 0
    const interval = setInterval(async () => {
      ticks++
      try {
        const ds = await datasetsApi.get(id)
        if (ds.status === 'scraping') {
          if (ticks > 5) updateStep(2, 'active')
        } else if (ds.status === 'ready') {
          clearInterval(interval)
          updateStep(1, 'done')
          updateStep(2, 'done')
          updateStep(3, 'done')
          setTimeout(() => router.push(`/datasets/${id}`), 800)
        } else if (ds.status === 'error') {
          clearInterval(interval)
          updateStep(1, 'error')
          setGlobalError(ds.error_message || 'Scraping failed.')
        }
      } catch {}
    }, 5000)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setInputError('')
    setGlobalError('')
    if (!input.trim()) { setInputError('Please enter a URL or ASIN.'); return }
    setLoading(true)
    updateStep(0, 'active')
    try {
      const res = await datasetsApi.create(input.trim())
      await pollStatus(res.id)
    } catch (err: any) {
      setLoading(false)
      updateStep(0, 'error')
      setGlobalError(err?.data?.message || 'Failed to create dataset.')
    }
  }

  const handleUpload = async (file: File) => {
    setUploadError('')
    setUploading(true)
    try {
      const res = await datasetsApi.upload(file)
      router.push(`/datasets/${res.id}`)
    } catch (err: any) {
      setUploading(false)
      setUploadError(err?.data?.message || 'Upload failed.')
    }
  }

  const StepIcon = ({ status }: { status: Step['status'] }) => {
    if (status === 'done') return <CheckCircle2 size={16} className="text-success" />
    if (status === 'active') return <Loader2 size={16} className="text-accent animate-spin" />
    if (status === 'error') return <Circle size={16} className="text-error" />
    return <Circle size={16} className="text-text-disabled" />
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'asin', label: 'Amazon URL or ASIN' },
    { id: 'csv', label: 'CSV' },
    { id: 'json', label: 'JSON' },
  ]

  return (
    <AuthGuard>
      <div className="flex flex-col min-h-screen">
        <TopNav />
        <main className="flex-1 px-6 py-6 max-w-2xl mx-auto w-full">
          <div className="flex items-center gap-3 mb-6">
            <Link href="/datasets" className="text-text-secondary hover:text-text-primary">
              <ArrowLeft size={18} />
            </Link>
            <h1 className="text-2xl font-semibold">New Dataset</h1>
          </div>

          <div className="bg-white border border-border rounded-xl p-6">
            {/* Scraping in-progress overlay */}
            {loading ? (
              <div className="space-y-4">
                <h2 className="font-medium text-text-primary">Scraping in progress…</h2>
                <div className="space-y-3">
                  {steps.map((step, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <StepIcon status={step.status} />
                      <span className={`text-sm ${step.status === 'pending' ? 'text-text-disabled' : step.status === 'error' ? 'text-error' : 'text-text-primary'}`}>
                        {step.label}
                      </span>
                      {step.status === 'done' && <span className="text-xs text-success ml-auto">Done</span>}
                      {step.status === 'active' && <span className="text-xs text-text-secondary ml-auto">In progress</span>}
                    </div>
                  ))}
                </div>
                {globalError && (
                  <div className="mt-4">
                    <p className="text-error text-sm mb-3">{globalError}</p>
                    <button
                      onClick={() => { setLoading(false); setSteps(steps.map(s => ({ ...s, status: 'pending' }))); setGlobalError('') }}
                      className="text-sm text-accent hover:underline"
                    >
                      Try again
                    </button>
                  </div>
                )}
                {!globalError && (
                  <p className="text-xs text-text-secondary pt-2">
                    This page will update automatically. You can also{' '}
                    <Link href="/datasets" className="text-accent hover:underline">go back to Datasets</Link> and return later.
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-5">
                {/* Tab header */}
                <div className="flex gap-1 border-b border-border">
                  {tabs.map(tab => (
                    <button
                      key={tab.id}
                      onClick={() => { setActiveTab(tab.id); setUploadError(''); setGlobalError('') }}
                      className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                        activeTab === tab.id
                          ? 'border-accent text-accent'
                          : 'border-transparent text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Amazon URL or ASIN tab */}
                {activeTab === 'asin' && (
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-text-primary mb-1" htmlFor="asin-input">
                        Amazon URL or ASIN
                      </label>
                      <input
                        id="asin-input"
                        type="text"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        placeholder="e.g. B08N5WRWNW or https://amazon.com/dp/B08N5WRWNW"
                        className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent font-mono"
                      />
                      {inputError && <p className="text-error text-xs mt-1" role="alert">{inputError}</p>}
                    </div>
                    {globalError && <p className="text-error text-sm" role="alert">{globalError}</p>}
                    <div className="flex gap-3 pt-1">
                      <button type="submit" className="bg-accent hover:bg-accent-hover text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors">
                        Start Scraping
                      </button>
                      <Link href="/datasets" className="px-5 py-2 text-sm border border-border rounded-lg hover:bg-raised transition-colors">
                        Cancel
                      </Link>
                    </div>
                  </form>
                )}

                {/* CSV upload tab */}
                {activeTab === 'csv' && (
                  <div className="space-y-4">
                    <p className="text-sm text-text-secondary">
                      Upload a CSV file exported from an Amazon review scraper. Required columns: <code className="text-xs bg-raised px-1 py-0.5 rounded">review_id</code>, <code className="text-xs bg-raised px-1 py-0.5 rounded">review_text</code>, <code className="text-xs bg-raised px-1 py-0.5 rounded">rating</code>.
                    </p>
                    <div>
                      <label className="block text-sm font-medium text-text-primary mb-1">CSV File</label>
                      <input
                        ref={csvRef}
                        type="file"
                        accept=".csv"
                        onChange={e => setCsvFile(e.target.files?.[0] ?? null)}
                        className="block w-full text-sm text-text-secondary file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-border file:text-sm file:bg-raised file:text-text-primary hover:file:bg-border cursor-pointer"
                      />
                      {csvFile && <p className="text-xs text-text-secondary mt-1">{csvFile.name} ({(csvFile.size / 1024).toFixed(1)} KB)</p>}
                    </div>
                    {uploadError && <p className="text-error text-sm" role="alert">{uploadError}</p>}
                    <div className="flex gap-3 pt-1">
                      <button
                        type="button"
                        disabled={!csvFile || uploading}
                        onClick={() => csvFile && handleUpload(csvFile)}
                        className="flex items-center gap-2 bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
                      >
                        {uploading ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
                        {uploading ? 'Uploading…' : 'Upload'}
                      </button>
                      <Link href="/datasets" className="px-5 py-2 text-sm border border-border rounded-lg hover:bg-raised transition-colors">
                        Cancel
                      </Link>
                    </div>
                  </div>
                )}

                {/* JSON upload tab */}
                {activeTab === 'json' && (
                  <div className="space-y-4">
                    <p className="text-sm text-text-secondary">
                      Upload a JSON file (array of review objects). Required fields: <code className="text-xs bg-raised px-1 py-0.5 rounded">review_id</code>, <code className="text-xs bg-raised px-1 py-0.5 rounded">review_text</code>, <code className="text-xs bg-raised px-1 py-0.5 rounded">rating</code>.
                    </p>
                    <div>
                      <label className="block text-sm font-medium text-text-primary mb-1">JSON File</label>
                      <input
                        ref={jsonRef}
                        type="file"
                        accept=".json"
                        onChange={e => setJsonFile(e.target.files?.[0] ?? null)}
                        className="block w-full text-sm text-text-secondary file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-border file:text-sm file:bg-raised file:text-text-primary hover:file:bg-border cursor-pointer"
                      />
                      {jsonFile && <p className="text-xs text-text-secondary mt-1">{jsonFile.name} ({(jsonFile.size / 1024).toFixed(1)} KB)</p>}
                    </div>
                    {uploadError && <p className="text-error text-sm" role="alert">{uploadError}</p>}
                    <div className="flex gap-3 pt-1">
                      <button
                        type="button"
                        disabled={!jsonFile || uploading}
                        onClick={() => jsonFile && handleUpload(jsonFile)}
                        className="flex items-center gap-2 bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
                      >
                        {uploading ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
                        {uploading ? 'Uploading…' : 'Upload'}
                      </button>
                      <Link href="/datasets" className="px-5 py-2 text-sm border border-border rounded-lg hover:bg-raised transition-colors">
                        Cancel
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}
