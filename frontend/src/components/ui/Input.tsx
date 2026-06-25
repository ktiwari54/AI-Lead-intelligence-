import { clsx } from 'clsx'
import { forwardRef, InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, helperText, className, id, ...props },
  ref
) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
        >
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        className={clsx(
          'input-base',
          error
            ? 'border-danger-500 focus:border-danger-500 focus:ring-danger-500'
            : '',
          className
        )}
        {...props}
      />
      {error && (
        <p className="mt-1 text-xs text-danger-600 dark:text-danger-400">{error}</p>
      )}
      {!error && helperText && (
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{helperText}</p>
      )}
    </div>
  )
})

export default Input
