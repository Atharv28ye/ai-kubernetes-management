'use client'

import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import {
  Clock,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

interface Investigation {
  id: string
  cluster: string
  root_cause: string
  explanation: string
  fix: string
  kubectl_commands: string[]
  confidence: number
  confidence_reasoning: string
  prevention: string
  namespace: string
  status: string
  created_at: string
  ai_generated?: boolean
}

export function InvestigationHistory() {

  const [investigations, setInvestigations] =
    useState<Investigation[]>([])

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState<string | null>(null)


  const fetchHistory = useCallback(
    async () => {

      try {

        setLoading(true)
        setError(null)

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL}/investigate/history?limit=10`,
          {
            cache: 'no-store',
          }
        )

        if (!response.ok) {

          const text =
            await response.text()

          throw new Error(
            text ||
            `Server returned ${response.status}`
          )
        }

        const data =
          await response.json()

        if (!data.success) {

          throw new Error(
            data.error ||
            'Failed to load history'
          )
        }

        setInvestigations(
          Array.isArray(
            data.investigations
          )
            ? data.investigations
            : []
        )

      } catch (err) {

        console.error(
          'Failed to fetch investigation history:',
          err
        )

        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load investigation history'
        )

      } finally {

        setLoading(false)

      }

    },
    []
  )


  useEffect(() => {

    fetchHistory()

  }, [fetchHistory])


  return (

    <section className="
      soft-card
      bg-white/60
      p-6
      sm:p-8
    ">

      {/* HEADER */}

      <div className="
        flex
        flex-col
        sm:flex-row
        sm:items-end
        sm:justify-between
        gap-4
        mb-7
      ">

        <div>

          <div className="
            flex
            items-center
            gap-2
            text-[#a77c8c]
          ">

            <Sparkles size={14} />

            <span className="
              text-xs
              uppercase
              tracking-[0.16em]
              font-bold
            ">
              Your archive
            </span>

          </div>

          <h2 className="
            font-serif
            text-3xl
            text-[#443d45]
            mt-1
          ">
            Recent investigations
          </h2>

        </div>


        <button
          onClick={fetchHistory}
          disabled={loading}
          className="
            inline-flex
            items-center
            justify-center
            gap-2
            rounded-full
            border
            border-[#ddced5]
            bg-white/70
            px-4
            py-2
            text-xs
            font-semibold
            text-[#756a73]
            hover:bg-white
            hover:-translate-y-0.5
            transition-all
            duration-300
            disabled:opacity-50
          "
        >

          <RefreshCw
            size={14}
            className={
              loading
                ? 'animate-spin'
                : ''
            }
          />

          {loading
            ? 'Loading...'
            : 'Refresh'}

        </button>

      </div>


      {/* LOADING */}

      {loading &&
        investigations.length === 0 && (

        <div className="
          py-12
          text-center
          text-sm
          text-[#8a8088]
        ">

          <div className="
            w-10
            h-10
            rounded-full
            bg-[#f5e4ea]
            flex
            items-center
            justify-center
            mx-auto
            mb-3
          ">

            <Sparkles
              size={17}
              className="text-[#b17c90]"
            />

          </div>

          Loading investigation history...

        </div>

      )}


      {/* ERROR */}

      {error && (

        <div className="
          rounded-2xl
          bg-[#fff1f3]
          border
          border-[#edc9d3]
          p-5
        ">

          <p className="
            text-sm
            font-semibold
            text-[#8e5265]
          ">
            Failed to load investigation history
          </p>

          <p className="
            text-xs
            text-[#9a6575]
            mt-1
          ">
            {error}
          </p>

          <button
            onClick={fetchHistory}
            className="
              mt-3
              text-xs
              font-semibold
              text-[#8e5265]
              underline
            "
          >
            Retry
          </button>

        </div>

      )}


      {/* EMPTY */}

      {!loading &&
        !error &&
        investigations.length === 0 && (

        <div className="
          rounded-2xl
          bg-[#f8f4fb]
          p-10
          text-center
        ">

          <div className="
            text-4xl
            text-[#c6b7d9]
            mb-3
          ">
            ♡
          </div>

          <p className="
            font-serif
            text-xl
            text-[#625967]
          ">
            Nothing here yet.
          </p>

          <p className="
            text-xs
            text-[#8b818a]
            mt-2
          ">
            Your future investigations will appear here.
          </p>

        </div>

      )}


      {/* CARDS */}

      {!error &&
        investigations.length > 0 && (

        <div className="
          columns-1
          md:columns-2
          gap-5
          space-y-5
        ">

          {investigations.map(
            investigation => (

            <article
              key={investigation.id}
              className="
                break-inside-avoid
                rounded-[22px]
                border
                border-[#e4d9de]
                bg-[#fffdf9]
                p-5
                hover:-translate-y-1
                hover:shadow-[0_18px_40px_rgba(75,60,75,0.09)]
                transition-all
                duration-300
              "
            >

              <div className="
                flex
                items-start
                justify-between
                gap-3
              ">

                <div className="min-w-0">

                  <div className="
                    flex
                    items-center
                    gap-2
                    flex-wrap
                  ">

                    <span className="
                      font-serif
                      text-lg
                      text-[#4b444c]
                    ">
                      {investigation.cluster ||
                        'Kubernetes Cluster'}
                    </span>

                    <span className="
                      text-[10px]
                      uppercase
                      tracking-wider
                      px-2
                      py-1
                      rounded-full
                      bg-[#e3f1e7]
                      text-[#66836f]
                      font-bold
                    ">
                      {investigation.status}
                    </span>

                  </div>

                </div>


                <ShieldCheck
                  size={18}
                  className="text-[#9ab3a0] flex-shrink-0"
                />

              </div>


              <div className="
                mt-4
                rounded-2xl
                bg-[#f8f2f6]
                p-4
              ">

                <p className="
                  text-sm
                  font-medium
                  leading-6
                  text-[#514950]
                ">
                  {investigation.root_cause ||
                    'No issues detected'}
                </p>

              </div>


              <div className="
                flex
                items-center
                justify-between
                gap-3
                mt-4
              ">

                <div className="
                  flex
                  items-center
                  gap-2
                  text-xs
                  text-[#8c828a]
                ">

                  <Clock size={13} />

                  {investigation.created_at
                    ? new Date(
                        investigation.created_at
                      ).toLocaleString()
                    : 'Unknown time'}

                </div>


                <div className="
                  text-right
                  flex-shrink-0
                ">

                  <div className="
                    font-serif
                    text-xl
                    text-[#bd7d96]
                  ">
                    {investigation.confidence != null
                      ? `${investigation.confidence}%`
                      : 'N/A'}
                  </div>

                  <div className="
                    text-[9px]
                    uppercase
                    tracking-wider
                    text-[#9a9098]
                  ">
                    confidence
                  </div>

                </div>

              </div>


              {investigation.explanation && (

                <p className="
                  mt-4
                  pt-4
                  border-t
                  border-[#eee4e8]
                  text-xs
                  leading-6
                  text-[#7b727a]
                  line-clamp-3
                ">
                  {investigation.explanation}
                </p>

              )}

            </article>

          ))}

        </div>

      )}

    </section>
  )
}