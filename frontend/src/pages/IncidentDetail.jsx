import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import {
  getIncident,
  getIncidentWorkflow,
  getIncidentAssignments,
  getIncidentHistory,
  releaseAssignment,
  updateIncidentStatus,
} from '../services/api'

const STATUS_LABELS = {
  pending: 'Pending',
  under_review: 'Under Review',
  confirmed: 'Confirmed',
  assigned: 'Assigned',
  in_progress: 'In Progress',
  resolved: 'Resolved',
  rejected: 'Rejected',
  merged: 'Merged',
}

const STATUS_STYLES = {
  pending: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  under_review: 'bg-blue-500/15 text-blue-300 ring-blue-500/30',
  confirmed: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  assigned: 'bg-purple-500/15 text-purple-300 ring-purple-500/30',
  in_progress: 'bg-cyan-500/15 text-cyan-300 ring-cyan-500/30',
  resolved: 'bg-green-500/15 text-green-300 ring-green-500/30',
  rejected: 'bg-red-500/15 text-red-300 ring-red-500/30',
  merged: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
}

function formatType(value) {
  if (!value) return 'Unknown'

  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${
        STATUS_STYLES[status] ||
        'bg-slate-500/15 text-slate-300 ring-slate-500/30'
      }`}
    >
      {STATUS_LABELS[status] || formatType(status)}
    </span>
  )
}

export default function IncidentDetail() {
  const { incidentId } = useParams()
  const navigate = useNavigate()

  const [incident, setIncident] = useState(null)
  const [workflow, setWorkflow] = useState(null)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(true)
  const [changingStatus, setChangingStatus] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [assignments, setAssignments] = useState([])
  const [history, setHistory] = useState([])
  const [releasingId, setReleasingId] = useState(null)

  const loadData = async () => {
    try {
      setLoading(true)
      setError('')

      const [incidentData, workflowData, assignmentData, historyData] =
        await Promise.all([
          getIncident(incidentId),
          getIncidentWorkflow(incidentId),
          getIncidentAssignments(incidentId),
          getIncidentHistory(incidentId),
        ])

      setIncident(incidentData)
      setWorkflow(workflowData)
      setAssignments(
        Array.isArray(assignmentData) ? assignmentData : [],
      )
      setHistory(historyData.history || [])
    } catch (err) {
      setError(
        err.userMessage ||
          err.response?.data?.detail ||
          'Unable to load incident',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [incidentId])

  const changeStatus = async (nextStatus) => {
    try {
      setChangingStatus(true)
      setError('')
      setSuccess('')

      const result = await updateIncidentStatus(
        incident.id,
        nextStatus,
        notes,
      )

      setIncident((current) => ({
        ...current,
        status: result.status || nextStatus,
        updated_at: result.updated_at || current.updated_at,
      }))

      setNotes('')
      setSuccess(
        `Incident status changed to ${
          STATUS_LABELS[nextStatus] || formatType(nextStatus)
        }.`,
      )

      await loadData()
    } catch (err) {
      setError(
        err.userMessage ||
          err.response?.data?.detail ||
          'Unable to change incident status',
      )
    } finally {
      setChangingStatus(false)
    }
  }

  const releaseResource = async (assignment) => {
    const confirmed = window.confirm(
      `Release ${assignment.quantity} unit(s) of ${assignment.resource_name}?`,
    )

    if (!confirmed) return

    try {
      setReleasingId(assignment.id)
      setError('')
      setSuccess('')

      await releaseAssignment(assignment.id, {
        notes: 'Released by Command Center operator.',
      })

      setSuccess(
        `${assignment.resource_name} released successfully.`,
      )

      await loadData()
    } catch (err) {
      setError(
        err.userMessage ||
          err.response?.data?.detail ||
          'Unable to release resource',
      )
    } finally {
      setReleasingId(null)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="text-sm text-slate-400">
          Loading incident...
        </div>
      </div>
    )
  }

  if (error && !incident) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-5 text-red-300">
        {error}
      </div>
    )
  }

  if (!incident) {
    return (
      <div className="rounded-xl border border-navy-700 bg-navy-900 p-5 text-slate-300">
        Incident not found.
      </div>
    )
  }

  const currentStatus = incident.status
  const currentWorkflow = workflow?.statuses?.find(
    (item) => item.status === currentStatus,
  )

  const allowedNext = currentWorkflow?.allowed_next || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <Link
            to="/incidents"
            className="text-sm text-orange-400 hover:text-orange-300"
          >
            ← Back to Incidents
          </Link>

          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold text-white">
              {incident.title || 'Emergency Incident'}
            </h1>

            <StatusBadge status={incident.status} />
          </div>

          <p className="mt-2 text-sm text-slate-400">
            {incident.incident_code || `Incident #${incident.id}`}
          </p>
        </div>

        <Link
          to={`/incidents/${incident.id}/response-plan`}
          className="inline-flex items-center justify-center rounded-lg bg-orange-600 px-4 py-2 text-sm font-semibold text-white hover:bg-orange-500"
        >
          Open Response Plan
        </Link>
      </div>

      {/* Alerts */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      {success && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-300">
          {success}
        </div>
      )}

      {/* Human approval banner */}
      <div className="rounded-xl border border-orange-500/30 bg-orange-500/10 p-4">
        <div className="font-semibold text-orange-300">
          Human Command Center Decision Required
        </div>
        <p className="mt-1 text-sm text-slate-300">
          AI analysis is advisory only. Operators must verify the incident
          before operational action is taken.
        </p>
      </div>

      {/* Incident overview */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-navy-700 bg-navy-900 p-5">
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Emergency Type
          </div>
          <div className="mt-2 font-semibold text-white">
            {formatType(incident.emergency_type)}
          </div>
        </div>

        <div className="rounded-xl border border-navy-700 bg-navy-900 p-5">
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Severity
          </div>
          <div className="mt-2 font-semibold text-orange-300">
            {formatType(incident.severity)}
          </div>
        </div>

        <div className="rounded-xl border border-navy-700 bg-navy-900 p-5">
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Reports
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            {incident.report_count ?? 0}
          </div>
        </div>

        <div className="rounded-xl border border-navy-700 bg-navy-900 p-5">
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Incident ID
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            #{incident.id}
          </div>
        </div>
      </div>

      {/* Status control */}
      <section className="rounded-xl border border-navy-700 bg-navy-900 p-5">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">
              Incident Workflow
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              Move the incident through the command-center workflow.
            </p>
          </div>

          <StatusBadge status={currentStatus} />
        </div>

        <div className="mt-5">
          <label className="mb-2 block text-sm font-medium text-slate-300">
            Operator notes
          </label>

          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={3}
            placeholder="Add verification or operational notes..."
            className="w-full rounded-lg border border-navy-600 bg-navy-950 px-3 py-2 text-sm text-white outline-none placeholder:text-slate-600 focus:border-orange-500"
          />
        </div>

        <div className="mt-5">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Allowed next actions
          </div>

          {allowedNext.length === 0 ? (
            <div className="rounded-lg border border-navy-700 bg-navy-950 p-4 text-sm text-slate-400">
              No manual status transition is available.
            </div>
          ) : (
            <div className="flex flex-wrap gap-3">
              {allowedNext.map((status) => (
                <button
                  key={status}
                  type="button"
                  disabled={changingStatus}
                  onClick={() => changeStatus(status)}
                  className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-orange-500 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {changingStatus
                    ? 'Updating...'
                    : `Mark ${STATUS_LABELS[status] || formatType(status)}`}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="mt-5 rounded-lg border border-navy-700 bg-navy-950 p-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Current status meaning
          </div>

          <p className="mt-2 text-sm text-slate-300">
            {currentWorkflow?.meaning ||
              'This incident is currently in the command workflow.'}
          </p>
        </div>
      </section>

      {/* Assigned Resources */}
      <section className="rounded-xl border border-navy-700 bg-navy-900 p-5">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">
              Assigned Resources
            </h2>

            <p className="mt-1 text-sm text-slate-400">
              Resources currently assigned to this incident.
            </p>
          </div>

          <Link
            to="/assignments"
            className="text-sm font-semibold text-orange-400 hover:text-orange-300"
          >
            View All Assignments →
          </Link>
        </div>

        {assignments.length === 0 ? (
          <div className="mt-4 rounded-lg border border-navy-700 bg-navy-950 p-4 text-sm text-slate-400">
            No resources are currently assigned to this incident.
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            {assignments.map((assignment) => (
              <div
                key={assignment.id}
                className="flex flex-col gap-4 rounded-lg border border-navy-700 bg-navy-950 p-4 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <div className="font-semibold text-white">
                    {assignment.resource_name}
                  </div>

                  <div className="mt-1 text-sm text-slate-400">
                    {assignment.resource_type} ·{' '}
                    {assignment.quantity} unit(s)
                  </div>

                  <div className="mt-1 text-xs text-slate-500">
                    Assigned{' '}
                    {assignment.assigned_at
                      ? new Date(
                          assignment.assigned_at,
                        ).toLocaleString()
                      : 'Unknown'}
                  </div>
                </div>

                <button
                  type="button"
                  disabled={releasingId === assignment.id}
                  onClick={() => releaseResource(assignment)}
                  className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm font-semibold text-red-300 hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {releasingId === assignment.id
                    ? 'Releasing...'
                    : 'Release Resource'}
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Incident information */}
      <section className="rounded-xl border border-navy-700 bg-navy-900 p-5">
        <h2 className="text-lg font-semibold text-white">
          Incident Information
        </h2>

        <div className="mt-4 grid gap-5 md:grid-cols-2">
          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500">
              Description
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              {incident.description || 'No description available.'}
            </p>
          </div>

          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500">
              Created
            </div>
            <p className="mt-2 text-sm text-slate-300">
              {incident.created_at
                ? new Date(incident.created_at).toLocaleString()
                : 'Unknown'}
            </p>

            <div className="mt-4 text-xs uppercase tracking-wide text-slate-500">
              Last Updated
            </div>
            <p className="mt-2 text-sm text-slate-300">
              {incident.updated_at
                ? new Date(incident.updated_at).toLocaleString()
                : 'Unknown'}
            </p>
          </div>
        </div>
      </section>

      {/* Timeline UI / Incident Activity */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-slate-900">
            Incident Activity
          </h2>
          <p className="text-sm text-slate-500">
            Audit trail of incident workflow and AI-related actions.
          </p>
        </div>

        {history.length === 0 ? (
          <div className="rounded-lg bg-slate-50 p-4 text-sm text-slate-500">
            No activity recorded yet.
          </div>
        ) : (
          <div className="space-y-4">
            {history.map((item) => (
              <div
                key={item.id}
                className="flex gap-4 border-l-2 border-slate-200 pl-4"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="font-medium text-slate-900">
                      {item.action ? item.action.replaceAll('_', ' ') : 'Action'}
                    </h3>

                    <span className="text-xs text-slate-500">
                      {item.created_at
                        ? new Date(item.created_at).toLocaleString()
                        : '—'}
                    </span>
                  </div>

                  {item.old_value && (
                    <p className="mt-1 text-sm text-slate-600">
                      Previous: {item.old_value}
                    </p>
                  )}

                  {item.new_value && (
                    <p className="text-sm text-slate-600">
                      New: {item.new_value}
                    </p>
                  )}

                  {item.notes && (
                    <p className="mt-2 rounded-lg bg-slate-50 p-2 text-sm text-slate-600">
                      {item.notes}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Actions */}
      <section className="grid gap-4 md:grid-cols-3">
        <Link
          to="/map"
          className="rounded-xl border border-navy-700 bg-navy-900 p-5 transition hover:border-orange-500/40"
        >
          <div className="text-lg font-semibold text-white">
            Emergency Map
          </div>
          <div className="mt-1 text-sm text-slate-400">
            View incident location and nearby emergency activity.
          </div>
        </Link>

        <Link
          to={`/incidents/${incident.id}/response-plan`}
          className="rounded-xl border border-navy-700 bg-navy-900 p-5 transition hover:border-orange-500/40"
        >
          <div className="text-lg font-semibold text-white">
            Response Plan
          </div>
          <div className="mt-1 text-sm text-slate-400">
            Generate and approve an AI-proposed response plan.
          </div>
        </Link>

        <Link
          to="/resources"
          className="rounded-xl border border-navy-700 bg-navy-900 p-5 transition hover:border-orange-500/40"
        >
          <div className="text-lg font-semibold text-white">
            Resources
          </div>
          <div className="mt-1 text-sm text-slate-400">
            Review simulated rescue resources and availability.
          </div>
        </Link>
      </section>
    </div>
  )
}