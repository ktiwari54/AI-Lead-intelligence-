'use client'

import { useState } from 'react'
import { Check, ChevronLeft, ChevronRight, Download } from 'lucide-react'
import { toast } from 'sonner'
import { useCreateExport, useExport, getExportDownloadUrl } from '@/hooks/useExports'
import { getToken } from '@/lib/auth'
import Button from '@/components/ui/Button'
import { cn } from '@/lib/utils'

const STEPS = ['Select', 'Configure', 'Download']

interface ExportWizardProps {
  onComplete?: () => void
}

export function ExportWizard({ onComplete }: ExportWizardProps) {
  const [step, setStep] = useState(0)
  const [entityType, setEntityType] = useState<'companies' | 'contacts' | 'leads'>('companies')
  const [format, setFormat] = useState<'CSV' | 'JSON' | 'EXCEL'>('CSV')
  const [name, setName] = useState('')
  const [exportId, setExportId] = useState('')

  const createExport = useCreateExport()
  const { data: exportJob } = useExport(exportId)

  const handleCreate = async () => {
    try {
      const job = await createExport.mutateAsync({
        name: name || `${entityType}-export-${Date.now()}`,
        format,
        entity_type: entityType,
        filters: {},
      })
      setExportId(job.id)
      setStep(2)
      onComplete?.()
      toast.success('Export queued')
    } catch {
      toast.error('Failed to create export')
    }
  }

  const handleDownload = async () => {
    const token = getToken()
    const url = getExportDownloadUrl(exportId)
    try {
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${name || 'export'}.${format === 'JSON' ? 'json' : format === 'EXCEL' ? 'xlsx' : 'csv'}`
      link.click()
      URL.revokeObjectURL(link.href)
      toast.success('Download started')
    } catch {
      toast.error('Export not ready yet — try again shortly')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            <div className={cn(
              'flex h-7 w-7 items-center justify-center rounded-full text-xs font-medium',
              i <= step ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
            )}>
              {i < step ? <Check className="h-3.5 w-3.5" /> : i + 1}
            </div>
            <span className={cn('text-sm', i === step ? 'font-medium' : 'text-muted-foreground')}>{label}</span>
            {i < STEPS.length - 1 && <ChevronRight className="h-4 w-4 text-muted-foreground" />}
          </div>
        ))}
      </div>

      {step === 0 && (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">What do you want to export?</p>
          <div className="grid gap-3 sm:grid-cols-3">
            {(['companies', 'contacts', 'leads'] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setEntityType(t)}
                className={cn(
                  'rounded-xl border p-4 text-left capitalize transition-colors',
                  entityType === t ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted/50'
                )}
              >
                <p className="font-medium text-foreground">{t}</p>
                <p className="text-xs text-muted-foreground mt-1">Export all {t}</p>
              </button>
            ))}
          </div>
          <div className="flex justify-end">
            <Button onClick={() => setStep(1)}>Next →</Button>
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="text-xs text-muted-foreground">Export name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={`${entityType}-export`}
              className="input-base mt-1 w-full max-w-md"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Format</label>
            <div className="mt-2 flex gap-2">
              {(['CSV', 'JSON', 'EXCEL'] as const).map((f) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => setFormat(f)}
                  className={cn(
                    'rounded-lg border px-4 py-2 text-sm',
                    format === f ? 'border-primary bg-primary/10 text-primary' : 'border-border'
                  )}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div className="flex justify-between">
            <Button variant="secondary" onClick={() => setStep(0)}>
              <ChevronLeft className="h-4 w-4 mr-1" /> Back
            </Button>
            <Button onClick={handleCreate} loading={createExport.isPending}>
              Create Export
            </Button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="rounded-xl border border-border p-8 text-center">
          {exportJob?.status === 'COMPLETED' ? (
            <>
              <Download className="mx-auto h-12 w-12 text-primary mb-3" />
              <h3 className="text-lg font-semibold text-foreground">Export Ready</h3>
              <p className="text-sm text-muted-foreground mt-1">
                {exportJob.row_count ?? 0} rows exported
              </p>
              <Button className="mt-4" onClick={handleDownload}>
                <Download className="h-4 w-4 mr-1.5" /> Download
              </Button>
            </>
          ) : exportJob?.status === 'FAILED' ? (
            <p className="text-destructive">Export failed. Please try again.</p>
          ) : (
            <>
              <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent mb-3" />
              <h3 className="text-lg font-semibold text-foreground">Processing Export</h3>
              <p className="text-sm text-muted-foreground mt-1">Status: {exportJob?.status ?? 'PENDING'}</p>
            </>
          )}
          <Button className="mt-4" variant="secondary" onClick={() => { setStep(0); setExportId('') }}>
            New Export
          </Button>
        </div>
      )}
    </div>
  )
}