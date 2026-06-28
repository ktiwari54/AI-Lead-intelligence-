'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Sparkles, PanelLeftClose, PanelLeft } from 'lucide-react'
import { cn } from '@/lib/utils'
import { mainNavigation, bottomNavigation } from '@/config/navigation'
import { useSidebarStore } from '@/stores/sidebar-store'
import { useCurrentUser } from '@/hooks/useAuth'
import { OrgSwitcher } from '@/components/enterprise/OrgSwitcher'
import { Badge } from '@/components/ui/Badge'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

function NavLink({
  name,
  href,
  icon: Icon,
  active,
  collapsed,
  badge,
  onNavigate,
}: {
  name: string
  href: string
  icon: React.ElementType
  active: boolean
  collapsed: boolean
  badge?: string
  onNavigate?: () => void
}) {
  return (
    <Link
      href={href}
      onClick={onNavigate}
      title={collapsed ? name : undefined}
      className={cn(
        'group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all',
        active
          ? 'bg-primary/10 text-primary shadow-sm'
          : 'text-muted-foreground hover:bg-accent hover:text-foreground',
        collapsed && 'justify-center px-2'
      )}
    >
      {active && (
        <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-primary" />
      )}
      <Icon className={cn('h-4 w-4 shrink-0', active && 'text-primary')} />
      {!collapsed && (
        <>
          <span className="truncate flex-1">{name}</span>
          {badge && (
            <Badge variant="secondary" className="h-5 px-1.5 text-[10px] font-semibold">
              {badge}
            </Badge>
          )}
        </>
      )}
    </Link>
  )
}

export function Sidebar() {
  const pathname = usePathname()
  const { collapsed, mobileOpen, setMobileOpen, toggleCollapsed } = useSidebarStore()
  const { data: user } = useCurrentUser()

  const initials = user?.full_name?.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase() ?? '?'
  const isActive = (href: string) => pathname === href || (href !== '/dashboard' && pathname.startsWith(href + '/'))

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-sidebar bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden
        />
      )}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-sidebar flex flex-col border-r border-border bg-card shadow-lg shadow-black/[0.03] transition-all duration-normal',
          collapsed ? 'w-sidebar-collapsed' : 'w-sidebar',
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <div className={cn('flex h-topbar items-center border-b border-border px-3', collapsed ? 'justify-center' : 'justify-between')}>
          <Link href="/dashboard" className="flex items-center gap-2.5 min-w-0">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-indigo-600 shadow-md shadow-primary/25">
              <Sparkles className="h-5 w-5 text-primary-foreground" />
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <p className="truncate text-sm font-bold text-foreground">Lead Intelligence</p>
                <p className="truncate text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Enterprise</p>
              </div>
            )}
          </Link>
          {!collapsed && (
            <button
              onClick={toggleCollapsed}
              className="hidden lg:flex rounded-lg p-2 text-muted-foreground hover:bg-accent hover:text-foreground"
              aria-label="Collapse sidebar"
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          )}
        </div>

        {collapsed && (
          <button
            onClick={toggleCollapsed}
            className="mx-auto mt-2 hidden lg:flex rounded-lg p-2 text-muted-foreground hover:bg-accent"
            aria-label="Expand sidebar"
          >
            <PanelLeft className="h-4 w-4" />
          </button>
        )}

        <div className={cn('px-2 py-3', collapsed && 'px-1')}>
          <OrgSwitcher collapsed={collapsed} />
        </div>

        <Separator />

        <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-5">
          {mainNavigation.map((section, i) => (
            <div key={i}>
              {section.title && !collapsed && (
                <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/80">
                  {section.title}
                </p>
              )}
              <div className="space-y-0.5">
                {section.items.map((item) => (
                  <NavLink
                    key={item.name}
                    {...item}
                    active={isActive(item.href)}
                    collapsed={collapsed}
                    onNavigate={() => setMobileOpen(false)}
                  />
                ))}
              </div>
            </div>
          ))}
        </nav>

        <Separator />

        <div className="px-2 py-3 space-y-0.5">
          {bottomNavigation.map((item) => (
            <NavLink
              key={item.name}
              {...item}
              active={isActive(item.href)}
              collapsed={collapsed}
              onNavigate={() => setMobileOpen(false)}
            />
          ))}
        </div>

        {user && (
          <div className={cn('border-t border-border p-3', collapsed && 'flex justify-center')}>
            <div className={cn('flex items-center gap-3', collapsed && 'justify-center')}>
              <Avatar className="h-9 w-9">
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
              {!collapsed && (
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-foreground">{user.full_name}</p>
                  <p className="truncate text-xs text-muted-foreground">{user.email}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </aside>
    </>
  )
}