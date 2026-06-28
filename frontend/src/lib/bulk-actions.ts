import { RowSelectionState } from '@tanstack/react-table'

export function getSelectedIds(selection: RowSelectionState): string[] {
  return Object.entries(selection)
    .filter(([, selected]) => selected)
    .map(([id]) => id)
}

export function exportToCsv<T extends Record<string, unknown>>(
  items: T[],
  columns: { key: keyof T; label: string }[],
  filename: string
) {
  const header = columns.map((c) => c.label).join(',')
  const rows = items.map((item) =>
    columns
      .map((c) => {
        const value = item[c.key]
        const str = value == null ? '' : String(value)
        return str.includes(',') || str.includes('"') ? `"${str.replace(/"/g, '""')}"` : str
      })
      .join(',')
  )
  const csv = [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}