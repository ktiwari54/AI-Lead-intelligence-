'use client'

import { ChevronsUpDown, Building2, Check } from 'lucide-react'
import { useCurrentUser } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export function OrgSwitcher({ collapsed }: { collapsed?: boolean }) {
  const { data: user } = useCurrentUser()
  const orgName = user?.organization?.name ?? 'Organization'

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className={collapsed ? 'h-9 w-9 p-0' : 'h-10 w-full justify-between px-2'}
          aria-label="Switch organization"
        >
          <span className="flex items-center gap-2 truncate">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary/10">
              <Building2 className="h-4 w-4 text-primary" />
            </span>
            {!collapsed && <span className="truncate text-sm font-medium">{orgName}</span>}
          </span>
          {!collapsed && <ChevronsUpDown className="h-4 w-4 shrink-0 text-muted-foreground" />}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        <DropdownMenuLabel>Organizations</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="gap-2">
          <Check className="h-4 w-4 text-primary" />
          {orgName}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled>Create organization</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}