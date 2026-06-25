import { clsx } from 'clsx'
import { ReactNode } from 'react'

type Variant = 'primary' | 'success' | 'warning' | 'danger' | 'gray'

interface BadgeProps {
  variant?: Variant
  children: ReactNode
  className?: string
}

const variantClasses: Record<Variant, string> = {
  primary: 'bg-primary-100 text-primary-700 dark:bg-primary-950 dark:text-primary-400',
  success: 'bg-success-100 text-success-700 dark:bg-green-950 dark:text-green-400',
  warning: 'bg-warning-100 text-warning-700 dark:bg-yellow-950 dark:text-yellow-400',
  danger: 'bg-danger-100 text-danger-700 dark:bg-red-950 dark:text-red-400',
  gray: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}

export default function Badge({
  variant = 'gray',
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  )
}
