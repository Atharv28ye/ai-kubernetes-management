'use client'

import { useEffect, useState } from 'react'
import { ChevronDown, Check, Server, Sparkles } from 'lucide-react'

interface Cluster {
  name: string
  cluster: string
  is_current: boolean
  server: string
}

interface ClusterSelectorProps {
  onClusterChange: (clusterName: string) => void
  selectedCluster: string | null
}

export function ClusterSelector({
  onClusterChange,
  selectedCluster,
}: ClusterSelectorProps) {

  const [clusters, setClusters] = useState<Cluster[]>([])
  const [loading, setLoading] = useState(true)
  const [switching, setSwitching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isOpen, setIsOpen] = useState(false)

  const fetchClusters = async () => {

    try {

      setError(null)

      const apiUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL

      if (!apiUrl) {
        throw new Error(
          'NEXT_PUBLIC_API_BASE_URL is not configured'
        )
      }

      const response = await fetch(
        `${apiUrl}/clusters/`,
        {
          cache: 'no-store',
        }
      )

      if (!response.ok) {
        throw new Error(
          `Failed to load clusters (${response.status})`
        )
      }

      const data = await response.json()

      if (
        !data.clusters ||
        data.clusters.length === 0
      ) {

        setClusters([])

        setError(
          'No Kubernetes clusters found in kubeconfig'
        )

        return
      }

      setClusters(data.clusters)

      if (!selectedCluster) {

        const current =
          data.clusters.find(
            (cluster: Cluster) =>
              cluster.is_current
          )

        if (current) {
          onClusterChange(current.name)
        } else {
          onClusterChange(
            data.clusters[0].name
          )
        }
      }

    } catch (err) {

      console.error(
        'Failed to fetch Kubernetes clusters:',
        err
      )

      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load clusters'
      )

    } finally {

      setLoading(false)

    }
  }

  useEffect(() => {

    fetchClusters()

    // eslint-disable-next-line react-hooks/exhaustive-deps

  }, [])

  const handleClusterSelect = async (
    clusterName: string
  ) => {

    if (
      clusterName === selectedCluster
    ) {

      setIsOpen(false)
      return

    }

    try {

      setSwitching(true)
      setError(null)

      const apiUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL

      if (!apiUrl) {
        throw new Error(
          'NEXT_PUBLIC_API_BASE_URL is not configured'
        )
      }

      const response = await fetch(
        `${apiUrl}/clusters/switch`,
        {
          method: 'POST',

          headers: {
            'Content-Type': 'application/json',
          },

          body: JSON.stringify({
            context_name: clusterName,
          }),
        }
      )

      const data = await response.json()

      if (
        !response.ok ||
        !data.success
      ) {

        throw new Error(
          data.detail ||
          data.error ||
          'Failed to switch cluster'
        )
      }

      onClusterChange(clusterName)

      setIsOpen(false)

      await fetchClusters()

    } catch (err) {

      console.error(
        'Failed to switch Kubernetes cluster:',
        err
      )

      setError(
        err instanceof Error
          ? err.message
          : 'Failed to switch cluster'
      )

    } finally {

      setSwitching(false)

    }
  }

  if (loading) {

    return (
      <div className="py-4">

        <div className="flex items-center gap-3 text-sm text-[#817985]">

          <div className="w-5 h-5 rounded-full border-2 border-[#d8bec9] border-t-transparent animate-spin" />

          Loading clusters...

        </div>

      </div>
    )
  }

  if (clusters.length === 0) {

    return (
      <div className="rounded-2xl bg-[#fff7e8] border border-[#ead9b3] p-4">

        <p className="text-sm font-medium text-[#826d45]">
          No Kubernetes clusters found.
        </p>

        <p className="text-xs text-[#9a845a] mt-1">
          Make sure Minikube or Kind is running.
        </p>

        {error && (
          <p className="text-xs text-red-600 mt-2">
            {error}
          </p>
        )}

      </div>
    )
  }

  const selectedClusterData =
    clusters.find(
      cluster =>
        cluster.name === selectedCluster
    ) ||
    clusters.find(
      cluster => cluster.is_current
    ) ||
    clusters[0]

  return (
    <div className="relative">

      <div className="flex items-center justify-between mb-2">

        <span className="text-xs uppercase tracking-[0.15em] font-semibold text-[#8d7781]">
          Active environment
        </span>

        <Sparkles
          size={14}
          className="text-[#c493a5]"
        />

      </div>


      <button
        type="button"
        onClick={() =>
          !switching &&
          setIsOpen(!isOpen)
        }
        disabled={switching}
        className="
          w-full
          flex
          items-center
          justify-between
          p-4
          rounded-2xl
          bg-white/70
          border
          border-[#ded0d6]
          hover:bg-white
          hover:border-[#cfa9b8]
          transition-all
          duration-300
          disabled:opacity-60
          text-left
        "
      >

        <div className="flex items-center min-w-0">

          <div
            className="
              w-10
              h-10
              rounded-full
              bg-[#f5dce5]
              flex
              items-center
              justify-center
              mr-3
              flex-shrink-0
            "
          >

            <Server
              size={17}
              className="text-[#a56e82]"
            />

          </div>


          <div className="min-w-0">

            <div className="font-medium text-[#494149] truncate">

              {switching
                ? 'Switching cluster...'
                : selectedClusterData?.name ||
                  'Select a cluster'}

            </div>

            {!switching &&
              selectedClusterData?.server && (

              <div className="text-xs text-[#928790] truncate mt-1">
                {selectedClusterData.server}
              </div>

            )}

          </div>

        </div>


        <ChevronDown
          size={18}
          className={`
            text-[#968993]
            transition-transform
            duration-300
            ${isOpen ? 'rotate-180' : ''}
          `}
        />

      </button>


      {isOpen && !switching && (

        <div className="
          absolute
          z-30
          w-full
          mt-2
          bg-[#fffdf9]
          border
          border-[#ded0d6]
          rounded-2xl
          shadow-[0_20px_50px_rgba(70,55,70,0.14)]
          overflow-hidden
          animate-fade-in
        ">

          {clusters.map(cluster => {

            const selected =
              cluster.name ===
              selectedClusterData?.name

            return (

              <button
                type="button"
                key={cluster.name}
                onClick={() =>
                  handleClusterSelect(
                    cluster.name
                  )
                }
                className={`
                  w-full
                  text-left
                  px-4
                  py-4
                  flex
                  items-center
                  gap-3
                  transition-all
                  duration-200
                  hover:bg-[#faf2f5]
                  ${
                    selected
                      ? 'bg-[#fdf0f4]'
                      : ''
                  }
                `}
              >

                <div
                  className={`
                    w-9
                    h-9
                    rounded-full
                    flex
                    items-center
                    justify-center
                    flex-shrink-0
                    ${
                      cluster.is_current
                        ? 'bg-[#dcefe3]'
                        : 'bg-[#eee9f4]'
                    }
                  `}
                >

                  <Server
                    size={15}
                    className={
                      cluster.is_current
                        ? 'text-[#6f947c]'
                        : 'text-[#887a96]'
                    }
                  />

                </div>


                <div className="flex-1 min-w-0">

                  <div className="flex items-center gap-2">

                    <span className="text-sm font-medium text-[#494149] truncate">
                      {cluster.name}
                    </span>

                    {cluster.is_current && (

                      <span className="text-[10px] uppercase tracking-wider text-[#6f947c] font-bold">
                        Current
                      </span>

                    )}

                  </div>

                  <div className="text-xs text-[#968b93] truncate mt-1">
                    {cluster.server}
                  </div>

                </div>


                {selected && (

                  <Check
                    size={18}
                    className="text-[#bb7c94] flex-shrink-0"
                  />

                )}

              </button>
            )
          })}

        </div>
      )}


      {error && (

        <div className="mt-2 text-xs text-red-600">
          {error}
        </div>

      )}

      <p className="mt-3 text-xs text-[#938890]">
        {clusters.length}{' '}
        {clusters.length === 1
          ? 'cluster'
          : 'clusters'}{' '}
        available
      </p>

    </div>
  )
}