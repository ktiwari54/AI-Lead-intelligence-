'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Fragment } from 'react'
import { Menu, Transition } from '@headlessui/react'
import {
  HomeIcon,
  BuildingOffice2Icon,
  UsersIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  Bars3Icon,
  XMarkIcon,
  BriefcaseIcon,
  ChevronDownIcon,
  BellIcon,
} from '@heroicons/react/24/outline'
import { clsx } from 'clsx'
import { useCurrentUser, useLogout } from '@/hooks/useAuth'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Companies', href: '/companies', icon: BuildingOffice2Icon },
  { name: 'Contacts', href: '/contacts', icon: UsersIcon },
  { name: 'Search', href: '/search', icon: MagnifyingGlassIcon },
  { name: 'AI Scoring', href: '/ai-scoring', icon: SparklesIcon },
  { name: 'CRM', href: '/crm', icon: BriefcaseIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pathname = usePathname()
  const { data: user } = useCurrentUser()
  const logout = useLogout()

  const initials = user
    ? `${user.full_name?.charAt(0) ?? ''}`.toUpperCase()
    : '?'

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col transition-transform duration-300 lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-800">
          <Link href="/dashboard" className="flex items-center gap-2">
            <SparklesIcon className="h-7 w-7 text-primary-600" />
            <span className="font-bold text-gray-900 dark:text-white text-sm leading-tight">
              AI Lead
              <br />
              Intelligence
            </span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navigation.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + '/')
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  active
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-950 dark:text-primary-400'
                    : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
                )}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* User info at bottom */}
        {user && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-800">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center text-white text-sm font-semibold">
                {initials}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {user.full_name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{user.email}</p>
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top header */}
        <header className="h-16 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between px-4 lg:px-6">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <Bars3Icon className="h-6 w-6" />
          </button>

          <div className="flex-1 lg:flex-none" />

          <div className="flex items-center gap-3">
            <button className="relative text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
              <BellIcon className="h-5 w-5" />
            </button>

            <Menu as="div" className="relative">
              <Menu.Button className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white rounded-lg px-2 py-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                <div className="h-7 w-7 rounded-full bg-primary-600 flex items-center justify-center text-white text-xs font-semibold">
                  {initials}
                </div>
                <span className="hidden sm:block font-medium">{user?.full_name ?? 'User'}</span>
                <ChevronDownIcon className="h-4 w-4" />
              </Menu.Button>

              <Transition
                as={Fragment}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 py-1 focus:outline-none z-50">
                  <Menu.Item>
                    {({ active }) => (
                      <Link
                        href="/settings/profile"
                        className={clsx(
                          'flex items-center gap-2 px-4 py-2 text-sm',
                          active
                            ? 'bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white'
                            : 'text-gray-700 dark:text-gray-300'
                        )}
                      >
                        Profile
                      </Link>
                    )}
                  </Menu.Item>
                  <div className="border-t border-gray-100 dark:border-gray-700 my-1" />
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={logout}
                        className={clsx(
                          'flex w-full items-center gap-2 px-4 py-2 text-sm',
                          active
                            ? 'bg-gray-50 dark:bg-gray-700 text-danger-600'
                            : 'text-gray-700 dark:text-gray-300'
                        )}
                      >
                        Sign out
                      </button>
                    )}
                  </Menu.Item>
                </Menu.Items>
              </Transition>
            </Menu>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
