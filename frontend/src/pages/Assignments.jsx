import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  getAssignments,
  releaseAssignment,
} from '../services/api'

export default function Assignments() {
  const [assignments, setAssignments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [releasingId, setReleasingId] = useState(null)
  const [message, setMessage] = useState('')

  const loadAssignments = useCallback(async () => {
    try {
      setError('')

      const data = await getAssignments({
        status: 'assigned',
        limit: 200,
      })

      setAssignments(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.userMessage || 'Failed to load assignments')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAssignments()

    const timer = setInterval(loadAssignments, 10000)

    return () => clearInterval(timer)
  }, [loadAssignments])

  const totalUnits = useMemo(
    () =>
      assignments.reduce(
        (sum, item) => sum + Number(item.quantity || 0),
        0,
      ),
    [assignments],
  )

  const releaseResource = async (assignment) => {
    const confirmed = window.confirm(
      `Release ${assignment.quantity} unit(s) of ${assignment.resource_name}?`,
    )

    if (!confirmed) return

    try {
      setReleasingId(assignment.id)
      setError('')
      setMessage('')

      const result = await releaseAssignment(assignment.id, {
        notes: 'Released by Command Center operator.',
      })

      setMessage(
        `${assignment.resource_name} released successfully. ` +
          `${result.quantity_returned || assignment.quantity} unit(s) returned to availability.`,
      )

      await loadAssignments()
    } catch (err) {
      setError(err.userMessage || 'Failed to release resource')
    } finally {
      setReleasingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-white">
              Resource Assignments
            </h1>

            <p className="mt-1 text-sm text-slate-400">
              Monitor resources currently assigned to emergency incidents.
            </p>
          </div>

          <Link
            to="/resources"
            className="rounded-lg border border-navy-700 bg-navy-900 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-navy-800"
          >
            View Resources
          </Link>
        </div>

        <div className="mt-3 rounded-lg border border-orange-500/20 bg-orange-500/10 px-4 py-3 text-sm text-orange-200">
          Resource assignment is simulated. Human approval is required;
          nothing is dispatched to real emergency services.
        </div>
      </div>

      {message && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
          {message}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-navy-700 bg-navy-900 p-5">
          <div className="text-sm text-slate-400">
            Active Assignments
          </div>

          <div className="mt-2 text-3xl font-bold text-white">
            {assignments.length}
          </div>
        </div>

        <div className="rounded-xl border border-navy-700 bg-navy-900 p-5">
          <div className="text-sm text-slate-400">
            Total Assigned Units
          </div>

          <div className="mt-2 text-3xl font-bold text-orange-400">
            {totalUnits}
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-navy-700 bg-navy-900">
        <div className="border-b border-navy-700 px-5 py-4">
          <h2 className="font-semibold text-white">
            Active Resource Assignments
          </h2>
        </div>

        {loading ? (
          <div className="p-6 text-sm text-slate-400">
            Loading assignments...
          </div>
        ) : assignments.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-lg font-semibold text-white">
              No active assignments
            </div>

            <p className="mt-2 text-sm text-slate-400">
              Approve a response plan to assign recommended resources.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-navy-700 bg-navy-950/50">
                <tr>
                  <th className="px-5 py-3 font-medium text-slate-400">
                    Incident
                  </th>
                  <th className="px-5 py-3 font-medium text-slate-400">
                    Resource
                  </th>
                  <th className="px-5 py-3 font-medium text-slate-400">
                    Type
                  </th>
                  <th className="px-5 py-3 font-medium text-slate-400">
                    Quantity
                  </th>
                  <th className="px-5 py-3 font-medium text-slate-400">
                    Assigned
                  </th>
                  <th className="px-5 py-3 font-medium text-slate-400">
                    Action
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-navy-700">
                {assignments.map((assignment) => (
                  <tr
                    key={assignment.id}
                    className="hover:bg-navy-800/40"
                  >
                    <td className="px-5 py-4">
                      <Link
                        to={`/incidents/${assignment.incident_id}`}
                        className="font-semibold text-orange-300 hover:text-orange-200"
                      >
                        {assignment.incident_code}
                      </Link>

                      <div className="mt-1 text-xs text-slate-500">
                        Incident #{assignment.incident_id}
                      </div>
                    </td>

                    <td className="px-5 py-4 font-medium text-white">
                      {assignment.resource_name}
                    </td>

                    <td className="px-5 py-4 text-slate-300">
                      {assignment.resource_type}
                    </td>

                    <td className="px-5 py-4">
                      <span className="rounded-full bg-orange-500/10 px-3 py-1 text-xs font-semibold text-orange-300">
                        {assignment.quantity}
                      </span>
                    </td>

                    <td className="px-5 py-4 text-slate-400">
                      {assignment.assigned_at
                        ? new Date(
                            assignment.assigned_at,
                          ).toLocaleString()
                        : '—'}
                    </td>

                    <td className="px-5 py-4">
                      <button
                        type="button"
                        onClick={() =>
                          releaseResource(assignment)
                        }
                        disabled={releasingId === assignment.id}
                        className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs font-semibold text-red-300 hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {releasingId === assignment.id
                          ? 'Releasing...'
                          : 'Release'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}