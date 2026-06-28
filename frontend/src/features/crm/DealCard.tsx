'use client'

import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical } from 'lucide-react'
import { CRMDeal } from '@/hooks/useCRM'
import { cn } from '@/lib/utils'

function formatCurrency(value?: number, currency = 'USD') {
  if (value == null) return null
  return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(value)
}

interface DealCardProps {
  deal: CRMDeal
  onClick?: () => void
}

export function DealCard({ deal, onClick }: DealCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: deal.id,
    data: { type: 'deal', deal },
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      onClick={onClick}
      className={cn(
        'rounded-lg border border-border bg-card p-3 shadow-sm transition-shadow hover:shadow-md',
        isDragging && 'scale-[1.02] shadow-lg opacity-90 z-10'
      )}
    >
      <div className="flex items-start gap-2">
        <button
          type="button"
          className="mt-0.5 cursor-grab text-muted-foreground hover:text-foreground active:cursor-grabbing"
          {...attributes}
          {...listeners}
          onClick={(e) => e.stopPropagation()}
          aria-label="Drag deal"
        >
          <GripVertical className="h-4 w-4" />
        </button>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm text-foreground truncate">{deal.name}</p>
          {deal.value != null && (
            <p className="text-primary font-semibold text-sm mt-0.5">
              {formatCurrency(deal.value, deal.currency)}
            </p>
          )}
          {deal.company_id && (
            <p className="text-xs text-muted-foreground mt-1 truncate">Company linked</p>
          )}
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground capitalize">
              {deal.status}
            </span>
            {deal.expected_close_date && (
              <span className="text-xs text-muted-foreground">
                {new Date(deal.expected_close_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}