import {
  LayoutDashboard,
  Building2,
  Users,
  Search,
  Sparkles,
  Bookmark,
  List,
  Target,
  Kanban,
  CheckSquare,
  Calendar,
  BarChart3,
  Upload,
  Download,
  Bell,
  Settings,
  Shield,
  HelpCircle,
  Brain,
  Plug,
  Key,
  CreditCard,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface NavItem {
  name: string
  href: string
  icon: LucideIcon
  permission?: string
  badge?: string
}

export interface NavSection {
  title?: string
  items: NavItem[]
}

export const mainNavigation: NavSection[] = [
  {
    items: [{ name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard }],
  },
  {
    title: 'Discover',
    items: [
      { name: 'Lead Discovery', href: '/search', icon: Search, badge: 'AI' },
      { name: 'Saved Searches', href: '/search/saved', icon: Bookmark },
      { name: 'Lists', href: '/lists', icon: List },
      { name: 'Segments', href: '/segments', icon: Target },
    ],
  },
  {
    title: 'Records',
    items: [
      { name: 'Companies', href: '/companies', icon: Building2 },
      { name: 'Contacts', href: '/contacts', icon: Users },
    ],
  },
  {
    title: 'Intelligence',
    items: [
      { name: 'AI Assistant', href: '/ai', icon: Brain },
      { name: 'Lead Scoring', href: '/ai-scoring', icon: Sparkles },
    ],
  },
  {
    title: 'CRM',
    items: [
      { name: 'Pipeline', href: '/crm', icon: Kanban },
      { name: 'Tasks', href: '/tasks', icon: CheckSquare },
      { name: 'Activities', href: '/activities', icon: Calendar },
      { name: 'Meetings', href: '/meetings', icon: Calendar },
    ],
  },
  {
    title: 'Analytics',
    items: [{ name: 'Reports', href: '/analytics', icon: BarChart3 }],
  },
  {
    title: 'Data Ops',
    items: [
      { name: 'Imports', href: '/imports', icon: Upload },
      { name: 'Exports', href: '/exports', icon: Download },
    ],
  },
]

export const bottomNavigation: NavItem[] = [
  { name: 'Notifications', href: '/notifications', icon: Bell },
  { name: 'Settings', href: '/settings', icon: Settings },
  { name: 'Admin', href: '/admin', icon: Shield, permission: 'admin:read' },
  { name: 'Help', href: '/help', icon: HelpCircle },
]

export const commandPaletteRoutes = [
  { label: 'Dashboard', href: '/dashboard', keywords: ['home', 'overview'] },
  { label: 'Companies', href: '/companies', keywords: ['records', 'accounts'] },
  { label: 'Contacts', href: '/contacts', keywords: ['people', 'leads'] },
  { label: 'Lead Discovery', href: '/search', keywords: ['discover', 'search', 'ai'] },
  { label: 'Saved Searches', href: '/search/saved', keywords: ['saved', 'bookmarks'] },
  { label: 'AI Assistant', href: '/ai', keywords: ['chat', 'assistant', 'help'] },
  { label: 'AI Scoring', href: '/ai-scoring', keywords: ['score', 'intelligence'] },
  { label: 'CRM Pipeline', href: '/crm', keywords: ['deals', 'pipeline', 'kanban'] },
  { label: 'Tasks', href: '/tasks', keywords: ['todo', 'follow-up'] },
  { label: 'Activities', href: '/activities', keywords: ['feed', 'timeline', 'history'] },
  { label: 'Meetings', href: '/meetings', keywords: ['calendar', 'demo', 'schedule'] },
  { label: 'Help', href: '/help', keywords: ['support', 'docs', 'guide'] },
  { label: 'Analytics', href: '/analytics', keywords: ['reports', 'charts'] },
  { label: 'Notifications', href: '/notifications', keywords: ['alerts', 'inbox'] },
  { label: 'Settings', href: '/settings', keywords: ['preferences', 'config'] },
  { label: 'Billing', href: '/settings', keywords: ['subscription', 'credits'] },
  { label: 'API Keys', href: '/settings', keywords: ['developer', 'keys'] },
  { label: 'Imports', href: '/imports', keywords: ['upload', 'csv'] },
  { label: 'Exports', href: '/exports', keywords: ['download', 'csv'] },
  { label: 'Admin', href: '/admin', keywords: ['audit', 'flags', 'system'] },
]

export const commandPaletteActions = [
  { label: 'Create new company', href: '/companies', keywords: ['add', 'new'] },
  { label: 'Start AI search', href: '/search', keywords: ['discover', 'find'] },
  { label: 'Open AI Assistant', href: '/ai', keywords: ['chat', 'help'] },
  { label: 'Export contacts', href: '/exports', keywords: ['download', 'csv'] },
]

export const settingsNavigation = [
  { name: 'Profile', href: '/settings', icon: Users },
  { name: 'Billing', href: '/settings', icon: CreditCard },
  { name: 'API Keys', href: '/settings', icon: Key },
]