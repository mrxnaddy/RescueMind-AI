import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import {
  getDuplicateCandidates,
  confirmDuplicate,
  rejectDuplicate,
} from '../services/api'

export default function DuplicateReview() {
  const [refreshKey, setRefreshKey] = useState(0)

  const candidates = useApi(
    () => getDuplicateCandidates({ status: 'pending', limit: 100 }),
    { intervalMs: 10000, refreshKey },
  )

  const handleAction = async (candidateId, action) => {
    try {
      if (action === 'confirm') {
        await confirmDuplicate(candidateId, {
          reviewer: 'Command Center',
        })
      } else {
        await rejectDuplicate(candidateId, {
          reviewer: 'Command Center',
        })
      }

      setRefreshKey((value) => value + 1)
    } catch (error) {
      window.alert(
        error.userMessage || 'Could not update duplicate candidate.',
      )
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">
          Duplicate Review
        </h1>
        <p className="text-sm text-slate-400">
          Review AI-generated duplicate suggestions before merging incidents.
        </p>
      </div>

      <div className="rounded-lg border border-orange-500/30 bg-orange-500/10 p-4 text-sm text-orange-300">
        AI suggestions are not verified facts. A human operator must
        confirm or reject every duplicate suggestion.
      </div>

      {candidates.error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-300">
          Could not load duplicate candidates:{' '}
          {candidates.error.userMessage}
        </div>
      )}

      {candidates.loading && !candidates.data && (
        <div className="text-slate-400">
          Loading duplicate candidates...
        </div>
      )}

      {candidates.data && candidates.data.length === 0 && (
        <div className="rounded-xl border border-navy-700 bg-navy-900 p-8 text-center">
          <div className="text-lg font-semibold text-white">
            No pending duplicates
          </div>
          <p className="mt-2 text-sm text-slate-400">
            There are currently no duplicate suggestions waiting for review.
          </p>
        </div>
      )}

      {candidates.data && candidates.data.length > 0 && (
        <div className="space-y-4">
          {candidates.data.map((candidate) => (
            <div
              key={candidate.id}
              className="rounded-xl border border-navy-700 bg-navy-900 p-5"
            >
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="space-y-3">
                  <div>
                    <div className="text-xs uppercase text-slate-500">
                      Candidate #{candidate.id}
                    </div>

                    <div className="mt-1 text-lg font-semibold text-white">
                      Duplicate similarity
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-3 text-sm">
                    <span className="rounded-lg bg-navy-950 px-3 py-2 text-slate-300">
                      Incident A:{' '}
                      <span className="font-mono text-white">
                        {candidate.incident_id_a}
                      </span>
                    </span>

                    <span className="rounded-lg bg-navy-950 px-3 py-2 text-slate-300">
                      Incident B:{' '}
                      <span className="font-mono text-white">
                        {candidate.incident_id_b}
                      </span>
                    </span>

                    <span className="rounded-lg bg-blue-500/10 px-3 py-2 text-blue-300">
                      Similarity:{' '}
                      {candidate.similarity_score != null
                        ? `${(candidate.similarity_score * 100).toFixed(1)}%`
                        : 'N/A'}
                    </span>
                  </div>

                  {candidate.reason && (
                    <p className="max-w-2xl text-sm text-slate-400">
                      {candidate.reason}
                    </p>
                  )}
                </div>

                <div className="flex shrink-0 gap-3">
                  <button
                    type="button"
                    onClick={() =>
                      handleAction(candidate.id, 'reject')
                    }
                    className="rounded-lg border border-navy-700 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-navy-800"
                  >
                    Reject
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      handleAction(candidate.id, 'confirm')
                    }
                    className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-500"
                  >
                    Confirm Duplicate
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}