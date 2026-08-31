'use client'

import { useState } from 'react'

import { InvestigateButton } from '@/components/InvestigateButton'
import { InvestigationProgress } from '@/components/InvestigationProgress'
import { RootCauseCard } from '@/components/RootCauseCard'
import { InvestigationHistory } from '@/components/InvestigationHistory'
import { ClusterSelector } from '@/components/ClusterSelector'

export default function Home() {
  const [isInvestigating, setIsInvestigating] = useState(false)

  const [investigationResult, setInvestigationResult] =
    useState<any>(null)

  const [progress, setProgress] = useState<string[]>([])

  const [investigationId, setInvestigationId] =
    useState<string | undefined>()

  const [selectedCluster, setSelectedCluster] =
    useState<string | null>(null)

  const [error, setError] =
    useState<string | null>(null)

  const handleInvestigate = async () => {
    if (!selectedCluster) {
      setError('Please select a Kubernetes cluster first')
      return
    }

    setIsInvestigating(true)

    setProgress([
      'Investigating Kubernetes Cluster...'
    ])

    setInvestigationResult(null)
    setInvestigationId(undefined)
    setError(null)

    try {
      setProgress([
        'Checking Pods...'
      ])

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/investigate/`,
        {
          method: 'POST',

          headers: {
            'Content-Type': 'application/json',
          },

          body: JSON.stringify({
            namespace: 'all',
            collect_logs: true,
            max_log_lines: 100,
            enable_ai: true,
            cluster: selectedCluster,
          }),
        }
      )

      const data = await response.json()

      if (!response.ok || data.status !== 'success') {
        throw new Error(
          data.error ||
          data.detail ||
          'Investigation failed'
        )
      }

      if (data.investigation_id) {
        setInvestigationId(
          data.investigation_id
        )
      }

      setProgress([
        '✓ Checking Pods',
        '✓ Reading Logs',
        '✓ Analyzing Events',
        '✓ Inspecting Deployments',
        '✓ Checking Networking',
        '✓ AI Reasoning',
        '✓ Root Cause Found',
      ])

      setInvestigationResult(data)

    } catch (err: any) {

      console.error(
        'Investigation error:',
        err
      )

      setProgress([
        'Investigation failed'
      ])

      setError(
        err?.message ||
        'Failed to connect to investigation service'
      )

    } finally {

      setIsInvestigating(false)

    }
  }

  return (
    <main className="min-h-screen relative overflow-hidden">

      {/* Decorative background */}

      <div className="pastel-orb orb-pink" />
      <div className="pastel-orb orb-lavender" />
      <div className="pastel-orb orb-blue" />

      <div className="app-shell">

        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-10 sm:py-16">

          {/* =========================
              HERO
          ========================= */}

          <header className="hero mb-12">

            <div className="hero-kicker">
              <span className="animate-pulse-soft">
                ✦
              </span>

              AI-powered infrastructure
            </div>

            <h1 className="hero-title">
              Kubernetes,
              <br />

              <span>but make it intelligent.</span>
            </h1>

            <p className="hero-subtitle">
              Investigate your Kubernetes clusters,
              understand what went wrong, and get
              AI-powered explanations without digging
              through endless logs.
            </p>

            <div className="flex flex-wrap gap-3 mt-6">

              <div className="px-4 py-2 rounded-full bg-white/70 border border-white shadow-sm text-xs text-gray-600">
                ☁ Multi-cluster
              </div>

              <div className="px-4 py-2 rounded-full bg-white/70 border border-white shadow-sm text-xs text-gray-600">
                ✦ AI diagnosis
              </div>

              <div className="px-4 py-2 rounded-full bg-white/70 border border-white shadow-sm text-xs text-gray-600">
                ♡ Real-time investigation
              </div>

            </div>

          </header>


          {/* =========================
              MAIN CONTROL CARD
          ========================= */}

          <section
            className="
              soft-card
              pastel-pink
              p-6
              sm:p-8
              mb-8
              animate-fade-up
            "
          >

            <div className="flex items-start gap-4 mb-7">

              <div
                className="
                  w-12
                  h-12
                  rounded-2xl
                  bg-white/80
                  flex
                  items-center
                  justify-center
                  text-xl
                  shadow-sm
                  animate-float
                "
              >
                ☁
              </div>

              <div>

                <h2 className="text-xl font-semibold text-gray-800">
                  Choose your cluster
                </h2>

                <p className="text-sm text-gray-500 mt-1">
                  Select the Kubernetes environment
                  you want to investigate.
                </p>

              </div>

            </div>

            <ClusterSelector
              onClusterChange={setSelectedCluster}
              selectedCluster={selectedCluster}
            />

            {/* Error */}

            {error && (

              <div
                className="
                  mt-5
                  bg-white/75
                  border
                  border-red-200
                  rounded-2xl
                  p-4
                  animate-fade-in
                "
              >

                <div className="flex items-start gap-3">

                  <div className="text-lg">
                    ♡
                  </div>

                  <div>

                    <h3 className="text-sm font-semibold text-red-800">
                      Something went wrong
                    </h3>

                    <p className="mt-1 text-sm text-red-700">
                      {error}
                    </p>

                  </div>

                </div>

              </div>

            )}

            {/* Investigate */}

            <div className="mt-7">

              <InvestigateButton
                onInvestigate={handleInvestigate}
                disabled={
                  isInvestigating ||
                  !selectedCluster
                }
              />

            </div>

          </section>


          {/* =========================
              INVESTIGATION PROGRESS
          ========================= */}

          {isInvestigating && (

            <section
              className="
                soft-card
                pastel-lavender
                p-6
                sm:p-8
                mb-8
                animate-fade-up
              "
            >

              <div className="flex items-center gap-3 mb-5">

                <div className="text-2xl animate-sparkle">
                  ✦
                </div>

                <div>

                  <h2 className="text-lg font-semibold text-gray-800">
                    Investigating your cluster
                  </h2>

                  <p className="text-sm text-gray-500">
                    The agent is looking for the story
                    behind the symptoms.
                  </p>

                </div>

              </div>

              <InvestigationProgress
                progress={progress}
                investigationId={investigationId}
              />

            </section>

          )}


          {/* =========================
              HEALTHY CLUSTER
          ========================= */}

          {investigationResult &&
            !investigationResult.diagnosis && (

            <section
              className="
                soft-card
                pastel-green
                p-7
                mb-8
                animate-fade-up
              "
            >

              <div className="flex items-start gap-4">

                <div
                  className="
                    w-12
                    h-12
                    rounded-full
                    bg-white/80
                    flex
                    items-center
                    justify-center
                    text-xl
                  "
                >
                  ✓
                </div>

                <div>

                  <h3 className="text-xl font-semibold text-green-900">
                    Your cluster looks healthy ✨
                  </h3>

                  <p className="mt-2 text-sm leading-6 text-green-700">
                    No critical Kubernetes issues were
                    detected during this investigation.
                  </p>

                </div>

              </div>

            </section>

          )}


          {/* =========================
              ROOT CAUSE
          ========================= */}

          {investigationResult &&
            investigationResult.diagnosis && (

            <section
              className="
                soft-card
                pastel-blue
                p-6
                sm:p-8
                mb-8
                animate-fade-up
              "
            >

              <div className="flex items-center gap-3 mb-6">

                <div
                  className="
                    w-11
                    h-11
                    rounded-2xl
                    bg-white/80
                    flex
                    items-center
                    justify-center
                    text-xl
                  "
                >
                  ✦
                </div>

                <div>

                  <h2 className="text-xl font-semibold text-gray-800">
                    Diagnosis
                  </h2>

                  <p className="text-sm text-gray-500 mt-1">
                    Here's what the investigation found.
                  </p>

                </div>

              </div>

              <RootCauseCard
                diagnosis={
                  investigationResult.diagnosis
                }
              />

            </section>

          )}


          {/* =========================
              HISTORY
          ========================= */}

          <section
            className="
              soft-card
              p-6
              sm:p-8
              animate-fade-up
            "
          >

            <div className="flex items-center gap-3 mb-6">

              <div
                className="
                  w-11
                  h-11
                  rounded-2xl
                  bg-[#f8dfe7]
                  flex
                  items-center
                  justify-center
                "
              >
                ♡
              </div>

              <div>

                <h2 className="text-xl font-semibold text-gray-800">
                  Investigation history
                </h2>

                <p className="text-sm text-gray-500 mt-1">
                  Previous cluster investigations.
                </p>

              </div>

            </div>

            <InvestigationHistory />

          </section>


          {/* =========================
              FOOTER
          ========================= */}

          <footer className="text-center py-10">

            <p className="text-xs text-gray-400">
              Built for curious engineers ✦
            </p>

          </footer>

        </div>

      </div>

    </main>
  )
}