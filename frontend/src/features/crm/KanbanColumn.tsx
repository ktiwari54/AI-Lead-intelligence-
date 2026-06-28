'use client'

import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CRMDeal, CRMStage } from '@/hooks/useCRM'
import { DealCard } from './DealCard'
import { cn } from '@/lib/utils'

interface KanbanColumnProps {
  stage: CRMStage
  deals: CRMDeal[]
  loading?: boolean
  onAddDeal?: (stageId: string) => void
}

export function KanbanColumn({ stage, deals, loading, onAddDeal }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: stage.id })

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex w-72 shrink-0 flex-col rounded-xl border border-border bg-muted/30 transition-colors',
        isOver && 'border-primary/50 bg-primary/5'
      )}
    >
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <span className="font-medium text-sm text-foreground">{stage.name}</span>
        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-semibold text-muted-foreground">
          {deals.length}
        </span>
      </div>

      <SortableContext items={deals.map((d) => d.id)} strategy={verticalListSortingStrategy}>
        <div className="flex-1 min-h-[120px] space-y-2 p-3">
          {loading ? (
            <div className="h-16 animate-pulse rounded-lg bg-muted" />
          ) : deals.length === 0 ? (
            <p className="py-4 text-center text-xs text-muted-foreground">No deals</p>
          ) : (
            deals.map((deal) => <DealCard key={deal.id} deal={deal} />)
          )}
        </div>
      </SortableContext>

      {onAddDeal && (
        <button
          type="button"
          onClick={() => onAddDeal(stage.id)}
          className="m-3 rounded-lg border border-dashed border-border py-2 text-sm text-muted-foreground hover:border-primary hover:text-primary transition-colors"
        >
          + Add Deal
        </button>
      )}
    </div>
  )
}