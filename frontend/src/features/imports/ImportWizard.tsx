'use client'

import { useState, useCallback } from 'react'
import { Upload, Check, ChevronRight, ChevronLeft } from 'lucide-react'
import { toast } from 'sonner'
import { parseCsv, COMPANY_FIELDS, CONTACT_FIELDS } from '@/lib/parse-csv'
import { useCreateImport } from '@/hooks/useExports'
import Button from '@/components/ui/Button'
import { cn } from '@/lib/utils'

const STEPS = ['Upload', 'Map', 'Preview', 'Import']

interface ImportWizardProps {
  onComplete?: (jobId: string) => void
}

export function ImportWizard({ onComplete }: ImportWizardProps) {
  const [step, setStep] = useState(0)
  const [entityType, setEntityType] = useState<'companies' | 'contacts'>('companies')
  const [fileName, setFileName] = useState('')
  const [headers, setHeaders] = useState<string[]>([])
  const [rows, setRows] = useState<string[][]>([])
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [jobId, setJobId] = useState<string | null>(null)

  const createImport = useCreateImport()
  const targetFields = entityType === 'companies' ? COMPANY_FIELDS : CONTACT_FIELDS

  const handleFile = useCallback((file: File) => {
    setFileName(file.name)
    const reader = new FileReader()
    reader.onload = (e) => {
      const parsed = parseCsv(String(e.target?.result ?? ''))
      setHeaders(parsed.headers)
      setRows(parsed.rows.slice(0, 100))
      const auto: Record<string, string> = {}
      targetFields.forEach((field) => {
        const match = parsed.headers.find(
          (h) => h.toLowerCase().replace(/\s/g, '_') === field || h.toLowerCase().includes(field.replace('_', ' '))
        )
        if (match) auto[field] = match
      })
      setMapping(auto)
      setStep(1)
    }
    reader.readAsText(file)
  }, [targetFields])

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleImport = async () => {
    try {
      const job = await createImport.mutateAsync({
        name: fileName || `Import ${entityType}`,
        entity_type: entityType,
        mapping,
      })
      setJobId(job.id)
      setStep(3)
      onComplete?.(job.id)
      toast.success('Import job started')
    } catch {
      toast.error('Import failed to start')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            <div className={cn(
              'flex h-7 w-7 items-center justify-center rounded-full text-xs font-medium',
              i < step ? 'bg-primary text-primary-foreground' :
              i === step ? 'bg-primary/20 text-primary ring-2 ring-primary' :
              'bg-muted text-muted-foreground'
            )}>
              {i < step ? <Check className="h-3.5 w-3.5" /> : i + 1}
            </div>
            <span className={cn('text-sm', i === step ? 'font-medium text-foreground' : 'text-muted-foreground')}>
              {label}
            </span>
            {i < STEPS.length - 1 && <ChevronRight className="h-4 w-4 text-muted-foreground" />}
          </div>
        ))}
      </div>

      {step === 0 && (
        <div className="space-y-4">
          <div className="flex gap-3">
            {(['companies', 'contacts'] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setEntityType(t)}
                className={cn(
                  'rounded-lg border px-4 py-2 text-sm capitalize',
                  entityType === t ? 'border-primary bg-primary/10 text-primary' : 'border-border'
                )}
              >
                {t}
              </button>
            ))}
          </div>
          <div
            onDrop={onDrop}
            onDragOver={(e) => e.preventDefault()}
            className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border py-16 hover:border-primary/50 transition-colors"
          >
            <Upload className="h-10 w-10 text-muted-foreground mb-3" />
            <p className="text-sm font-medium text-foreground">Drag & drop CSV file here</p>
            <p className="text-xs text-muted-foreground mt-1">or</p>
            <label className="mt-3 cursor-pointer rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90">
              Browse Files
              <input
                type="file"
                accept=".csv,.txt"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
            </label>
            <p className="mt-3 text-xs text-muted-foreground">Supported: .csv (max 50MB)</p>
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Map CSV columns to {entityType} fields</p>
          <div className="rounded-xl border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Field</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">CSV Column</th>
                </tr>
              </thead>
              <tbody>
                {targetFields.map((field) => (
                  <tr key={field} className="border-t border-border">
                    <td className="px-4 py-2 font-medium capitalize">{field.replace(/_/g, ' ')}</td>
                    <td className="px-4 py-2">
                      <select
                        value={mapping[field] ?? ''}
                        onChange={(e) => setMapping((m) => ({ ...m, [field]: e.target.value }))}
                        className="input-base text-sm w-full max-w-xs"
                      >
                        <option value="">— Skip —</option>
                        {headers.map((h) => (
                          <option key={h} value={h}>{h}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex justify-between">
            <Button variant="secondary" onClick={() => setStep(0)}>
              <ChevronLeft className="h-4 w-4 mr-1" /> Back
            </Button>
            <Button onClick={() => setStep(2)}>Preview →</Button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Preview first {Math.min(rows.length, 5)} of {rows.length} rows
          </p>
          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  {targetFields.filter((f) => mapping[f]).map((f) => (
                    <th key={f} className="px-3 py-2 text-left text-xs font-medium text-muted-foreground capitalize">
                      {f.replace(/_/g, ' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 5).map((row, ri) => (
                  <tr key={ri} className="border-t border-border">
                    {targetFields.filter((f) => mapping[f]).map((f) => {
                      const colIdx = headers.indexOf(mapping[f])
                      return (
                        <td key={f} className="px-3 py-2 text-muted-foreground">
                          {row[colIdx] ?? '—'}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex justify-between">
            <Button variant="secondary" onClick={() => setStep(1)}>
              <ChevronLeft className="h-4 w-4 mr-1" /> Back
            </Button>
            <Button onClick={handleImport} loading={createImport.isPending}>
              Start Import
            </Button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="rounded-xl border border-border bg-card p-8 text-center">
          <Check className="mx-auto h-12 w-12 text-success mb-3" />
          <h3 className="text-lg font-semibold text-foreground">Import Started</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Processing {rows.length} rows from {fileName}
          </p>
          {jobId && (
            <p className="mt-1 text-xs text-muted-foreground">Job ID: {jobId}</p>
          )}
          <Button className="mt-4" variant="secondary" onClick={() => { setStep(0); setJobId(null) }}>
            Import Another File
          </Button>
        </div>
      )}
    </div>
  )
}