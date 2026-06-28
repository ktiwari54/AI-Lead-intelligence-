'use client'

import { useMemo, useState } from 'react'
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragEndEvent,
} from '@dnd-kit/core'
import { CRMDeal, CRMStage, useUpdateDeal } from '@/hooks/useCRM'
import { KanbanColumn } from './KanbanColumn'
import { DealCard } from './DealCard'
import { toast } from 'sonner'

interface KanbanBoardProps {
  stages: CRMStage[]
  deals: CRMDeal[]
  loading?: boolean
  onAddDeal?: (stageId: string) => void
}

export function KanbanBoard({ stages, deals, loading, onAddDeal }: KanbanBoardProps) {
  const [activeId, setActiveId] = useState<string | null>(null)
  const updateDeal = useUpdateDeal()

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor)
  )

  const dealsByStage = useMemo(() => {
    const map: Record<string, CRMDeal[]> = {}
    stages.forEach((s) => { map[s.id] = [] })
    deals.forEach((d) => {
      if (map[d.stage_id]) map[d.stage_id].push(d)
    })
    return map
  }, [stages, deals])

  const activeDeal = activeId ? deals.find((d) => d.id === activeId) : null

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(String(event.active.id))
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveId(null)
    const { active, over } = event
    if (!over) return

    const dealId = String(active.id)
    const deal = deals.find((d) => d.id === dealId)
    if (!deal) return

    let targetStageId = over.id as string
    if (!stages.some((s) => s.id === targetStageId)) {
      const overDeal = deals.find((d) => d.id === targetStageId)
      if (overDeal) targetStageId = overDeal.stage_id
    }

    if (deal.stage_id === targetStageId) return

    try {
      await updateDeal.mutateAsync({ id: dealId, stage_id: targetStageId })
      toast.success('Deal moved')
    } catch {
      toast.error('Failed to move deal')
    }
  }

  const totalValue = deals.reduce((sum, d) => sum + (d.value ?? 0), 0)

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        {deals.length} deals · {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(totalValue)} pipeline
      </p>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 overflow-x-auto pb-4">
          {stages.map((stage) => (
            <KanbanColumn
              key={stage.id}
              stage={stage}
              deals={dealsByStage[stage.id] ?? []}
              loading={loading}
              onAddDeal={onAddDeal}
            />
          ))}
        </div>

        <DragOverlay>
          {activeDeal ? (
            <div className="w-72 opacity-95">
              <DealCard deal={activeDeal} />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  )
}