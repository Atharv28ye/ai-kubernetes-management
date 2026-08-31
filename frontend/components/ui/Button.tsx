import {
  ButtonHTMLAttributes,
  forwardRef,
} from 'react'

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline'
  size?: 'default' | 'sm' | 'lg'
}

export const Button = forwardRef<
  HTMLButtonElement,
  ButtonProps
>(
  (
    {
      className = '',
      variant = 'default',
      size = 'default',
      ...props
    },
    ref
  ) => {

    const baseStyles =
      'pastel-button inline-flex items-center justify-center rounded-full font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#d9aabd] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50'

    const variantStyles = {
      default:
        'bg-[#4d444c] text-white hover:bg-[#39333a] shadow-[0_8px_25px_rgba(77,68,76,0.16)]',

      outline:
        'border border-[#d9c8d0] bg-white/70 text-[#514850] hover:bg-white',
    }

    const sizeStyles = {
      default:
        'h-11 px-6 py-2',

      sm:
        'h-9 px-4 text-sm',

      lg:
        'h-12 px-8',
    }

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'