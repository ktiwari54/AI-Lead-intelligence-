'use client'

import { useCurrentUser } from '@/hooks/useAuth'
import { useCompanies } from '@/hooks/useCompanies'
import { useContacts } from '@/hooks/useContacts'
import Link from 'next/link'
import {
  BuildingOffice2Icon,
  UsersIcon,
  SparklesIcon,
  CreditCardIcon,
  MagnifyingGlassIcon,
  ArrowUpTrayIcon,
  ArrowDownTrayIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

function StatCard({
  title,
  value,
  icon: Icon,
  change,
  color = 'primary',
}: {
  title: string
  value: string | number
  icon: React.ElementType
  change?: { value: number; label: string }
  color?: 'primary' | 'success' | 'warning' | 'danger'
}) {
  const colorMap = {
    primary: 'bg-primary-50 text-primary-600 dark:bg-primary-950 dark:text-primary-400',
    success: 'bg-success-50 text-success-600 dark:bg-green-950 dark:text-green-400',
    warning: 'bg-warning-50 text-warning-600 dark:bg-yellow-950 dark:text-yellow-400',
    danger: 'bg-danger-50 text-danger-600 dark:bg-red-950 dark:text-red-400',
  }

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
          {change && (
            <p className={clsx(
              'mt-1 text-xs flex items-center gap-1',
              change.value >= 0 ? 'text-success-600' : 'text-danger-600'
            )}>
              <ArrowTrendingUpIcon className="h-3.5 w-3.5" />
              {change.value >= 0 ? '+' : ''}{change.value}% {change.label}
            </p>
          )}
        </div>
        <div className={clsx('h-12 w-12 rounded-xl flex items-center justify-center', colorMap[color])}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  )
}

const recentActivity = [
  { id: 1, action: 'New company added', target: 'Acme Corp', time: '2 minutes ago', type: 'company' },
  { id: 2, action: 'AI score generated', target: 'TechStart Inc', time: '15 minutes ago', type: 'score' },
  { id: 3, action: 'Contact updated', target: 'John Doe', time: '1 hour ago', type: 'contact' },
  { id: 4, action: 'Search completed', target: 'SaaS companies in US', time: '2 hours ago', type: 'search' },
  { id: 5, action: 'Export finished', target: '250 companies exported', time: '3 hours ago', type: 'export' },
]

export default function DashboardPage() {
  const { data: user } = useCurrentUser()
  const { data: companies } = useCompanies({ per_page: 1 })
  const { data: contacts } = useContacts({ per_page: 1 })

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Welcome back, {user?.full_name?.split(' ')[0] ?? 'there'}
        </h1>
        <p className="mt-1 text-gray-500 dark:text-gray-400">
          Here&apos;s what&apos;s happening with your leads today.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Companies"
          value={companies?.total ?? 0}
          icon={BuildingOffice2Icon}
          color="primary"
          change={{ value: 12, label: 'this month' }}
        />
        <StatCard
          title="Total Contacts"
          value={contacts?.total ?? 0}
          icon={UsersIcon}
          color="success"
          change={{ value: 8, label: 'this month' }}
        />
        <StatCard
          title="AI Scores Generated"
          value="1,284"
          icon={SparklesIcon}
          color="warning"
          change={{ value: 23, label: 'this week' }}
        />
        <StatCard
          title="Credits Remaining"
          value={user?.organization?.credits ?? 0}
          icon={CreditCardIcon}
          color="danger"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-800">
            <h2 className="font-semibold text-gray-900 dark:text-white">Recent Activity</h2>
            <Link
              href="/activity"
              className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
            >
              View all
            </Link>
          </div>
          <ul className="divide-y divide-gray-100 dark:divide-gray-800">
            {recentActivity.map((item) => (
              <li key={item.id} className="px-5 py-3.5 flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-900 dark:text-white">
                    <span className="text-gray-500 dark:text-gray-400">{item.action}: </span>
                    <span className="font-medium">{item.target}</span>
                  </p>
                </div>
                <span className="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap ml-4">
                  {item.time}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
          <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-800">
            <h2 className="font-semibold text-gray-900 dark:text-white">Quick Actions</h2>
          </div>
          <div className="p-4 space-y-3">
            <Link
              href="/search"
              className="flex items-center gap-3 w-full p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <div className="h-9 w-9 rounded-lg bg-primary-50 dark:bg-primary-950 flex items-center justify-center">
                <MagnifyingGlassIcon className="h-5 w-5 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">New Search</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Find leads with AI</p>
              </div>
            </Link>

            <Link
              href="/companies?action=import"
              className="flex items-center gap-3 w-full p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <div className="h-9 w-9 rounded-lg bg-success-50 dark:bg-green-950 flex items-center justify-center">
                <ArrowUpTrayIcon className="h-5 w-5 text-success-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Import Data</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Upload CSV or Excel</p>
              </div>
            </Link>

            <Link
              href="/companies?action=export"
              className="flex items-center gap-3 w-full p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <div className="h-9 w-9 rounded-lg bg-warning-50 dark:bg-yellow-950 flex items-center justify-center">
                <ArrowDownTrayIcon className="h-5 w-5 text-warning-600 dark:text-yellow-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Export Data</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Download your leads</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
