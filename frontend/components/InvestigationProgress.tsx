'use client'

import { useEffect, useState } from 'react'
import {
  Check,
  Loader2,
  Sparkles,
} from 'lucide-react'

interface InvestigationProgressProps {
  progress: string[]
  investigationId?: string
}

export function InvestigationProgress({
  progress,
  investigationId,
}: InvestigationProgressProps) {

  const [elapsedSeconds, setElapsedSeconds] =
    useState(0)

  useEffect(() => {

    const interval = setInterval(() => {

      setElapsedSeconds(
        seconds => seconds + 1
      )

    }, 1000)

    return () =>
      clearInterval(interval)

  }, [])

  return (

    <div className="
      soft-card
      pastel-blue
      p-6
      sm:p-7
    ">

      {/* HEADER */}

      <div className="flex items-center justify-between mb-6">

        <div>

          <p className="text-xs uppercase tracking-[0.15em] text-[#7995a5] font-semibold">
            Live analysis
          </p>

          <h2 className="font-serif text-2xl text-[#454047] mt-1">
            Investigating cluster
          </h2>

        </div>

        <div className="
          w-11
          h-11
          rounded-full
          bg-white/70
          flex
          items-center
          justify-center
          animate-progress-glow
        ">

          <Sparkles
            size={18}
            className="text-[#9b88b5]"
          />

        </div>

      </div>


      {/* TIMER */}

      <div className="
        flex
        items-center
        justify-between
        bg-white/55
        rounded-2xl
        px-4
        py-3
        mb-6
      ">

        <span className="text-xs text-[#817b84]">
          Elapsed time
        </span>

        <span className="font-mono text-sm font-semibold text-[#5c5260]">
          {elapsedSeconds}s
        </span>

      </div>


      {/* ID */}

      {investigationId && (

        <div className="
          mb-6
          text-xs
          text-[#817b84]
          bg-white/45
          rounded-xl
          px-3
          py-2
        ">

          Investigation ID:{' '}

          <span className="font-mono text-[#665b68]">
            {investigationId}
          </span>

        </div>

      )}


      {/* TIMELINE */}

      <div className="relative">

        <div className="
          absolute
          left-[15px]
          top-3
          bottom-3
          w-px
          bg-[#cddde6]
        " />


        <div className="space-y-5">

          {progress.length === 0 ? (

            <div className="flex items-center gap-4">

              <div className="
                relative
                z-10
                w-8
                h-8
                rounded-full
                bg-white
                flex
                items-center
                justify-center
              ">

                <Loader2
                  size={15}
                  className="animate-spin text-[#a082b5]"
                />

              </div>

              <span className="text-sm text-[#756d76]">
                Starting investigation...
              </span>

            </div>

          ) : (

            progress.map((item, index) => {

              const completed =
                item.startsWith('✓') ||
                item.includes('Checking') ||
                item.includes('Reading') ||
                item.includes('Analyzing') ||
                item.includes('Inspecting') ||
                item.includes('Reasoning') ||
                item.includes('Found')

              return (

                <div
                  key={`${item}-${index}`}
                  className="
                    relative
                    flex
                    items-center
                    gap-4
                    animate-fade-up
                  "
                  style={{
                    animationDelay:
                      `${index * 70}ms`,
                  }}
                >

                  <div
                    className={`
                      relative
                      z-10
                      w-8
                      h-8
                      rounded-full
                      flex
                      items-center
                      justify-center
                      flex-shrink-0
                      ${
                        completed
                          ? 'bg-[#e0f0e5]'
                          : 'bg-white'
                      }
                    `}
                  >

                    {completed ? (

                      <Check
                        size={15}
                        className="text-[#71937c]"
                      />

                    ) : (

                      <Loader2
                        size={14}
                        className="animate-spin text-[#a48ab7]"
                      />

                    )}

                  </div>


                  <span
                    className={`
                      text-sm
                      ${
                        completed
                          ? 'text-[#5d565f] font-medium'
                          : 'text-[#857b84]'
                      }
                    `}
                  >

                    {item.replace(/^✓\s*/, '')}

                  </span>

                </div>

              )
            })

          )}

        </div>

      </div>

    </div>
  )
}