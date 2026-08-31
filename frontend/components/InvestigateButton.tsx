import { Sparkles, ArrowUpRight } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface InvestigateButtonProps {
  onInvestigate: () => void
  disabled: boolean
}

export function InvestigateButton({
  onInvestigate,
  disabled,
}: InvestigateButtonProps) {

  return (
    <Button
      onClick={onInvestigate}
      disabled={disabled}
      className="
        group
        w-full
        h-14
        rounded-full
        text-[15px]
        tracking-wide
        relative
        overflow-hidden
      "
    >

      <span className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-r from-transparent via-white/10 to-transparent" />

      <span className="relative flex items-center justify-center gap-3">

        <Sparkles
          size={18}
          className="transition-transform duration-300 group-hover:rotate-12 group-hover:scale-110"
        />

        <span>
          {disabled
            ? 'Investigating...'
            : 'Investigate Cluster'}
        </span>

        {!disabled && (
          <ArrowUpRight
            size={17}
            className="transition-transform duration-300 group-hover:translate-x-1 group-hover:-translate-y-1"
          />
        )}

      </span>

    </Button>
  )
}