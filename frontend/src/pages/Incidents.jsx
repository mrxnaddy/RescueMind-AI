import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getIncidents } from '../services/api'
import { SeverityBadge, StatusBadge } from '../components/Badges'
import { formatDateTime } from '../utils/format'

export default function Incidents() {
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [emergencyType, setEmergencyType] = useState('')

  const params = useMemo(
    () => ({
      limit: 100,
      ...(severity ? { severity } : {}),
      ...(status ? { status } : {}),
      ...(emergencyType ? { emergency_type: emergencyType } : {}),
    }),
    [severity, status, emergencyType],
  )

  const incidents = useApi(
    () => getIncidents(params),
    { intervalMs: 10000 },
  )

  const clearFilters = () => {
    setSeverity('')
    setStatus('')
    setEmergencyType('')
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Incidents</h1>
        <p className="text-sm text-slate-400">
          Review active emergency incidents from the backend.
        </p>
      </div>

      <div className="rounded-xl border border-navy-700 bg-navy-900 p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-400">
              Severity
            </label>
            <select
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
              className="rounded-lg border border-navy-700 bg-navy-950 px-3 py-2 text-sm text-white outline-none"
            >
              <option value="">All severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-400">
              Status
            </label>
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="rounded-lg border border-navy-700 bg-navy-950 px-3 py-2 text-sm text-white outline-none"
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In progress</option>
              <option value="resolved">Resolved</option>
              <option value="merged">Merged</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-400">
              Emergency type
            </label>
            <select
              value={emergencyType}
              onChange={(event) => setEmergencyType(event.target.value)}
              className="rounded-lg border border-navy-700 bg-navy-950 px-3 py-2 text-sm text-white outline-none"
            >
              <option value="">All types</option>
              <option value="flood">Flood</option>
              <option value="earthquake">Earthquake</option>
              <option value="fire">Fire</option>
              <option value="road_accident">Road accident</option>
              <option value="medical">Medical</option>
            </select>
          </div>

          <button
            type="button"
            onClick={clearFilters}
            className="rounded-lg border border-navy-700 px-3 py-2 text-sm text-slate-300 hover:bg-navy-800"
          >
            Clear filters
          </button>
        </div>
      </div>

      {incidents.error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-300">
          Could not load incidents: {incidents.error.userMessage}
        </div>
      )}

      {incidents.loading && !incidents.data && (
        <div className="text-slate-400">Loading incidents...</div>
      )}

      {incidents.data && incidents.data.length === 0 && (
        <div className="rounded-xl border border-navy-700 bg-navy-900 p-8 text-center text-slate-400">
          No incidents match the selected filters.
        </div>
      )}

      {incidents.data && incidents.data.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-navy-700 bg-navy-900">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-navy-700 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-3">Code</th>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Reports</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3">Action</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-navy-700">
                {incidents.data.map((incident) => (
                  <tr key={incident.id} className="hover:bg-navy-800/50">
                    <td className="px-4 py-3 font-mono text-xs text-slate-300">
                      {incident.incident_code}
                    </td>

                    <td className="max-w-[18rem] px-4 py-3 text-slate-200">
                      <div className="truncate">{incident.title}</div>
                    </td>

                    <td className="px-4 py-3 text-slate-300">
                      {incident.emergency_type?.replaceAll('_', ' ')}
                    </td>

                    <td className="px-4 py-3">
                      <SeverityBadge severity={incident.severity} />
                    </td>

                    <td className="px-4 py-3">
                      <StatusBadge status={incident.status} />
                    </td>

                    <td className="px-4 py-3 text-slate-300">
                      {incident.report_count}
                    </td>

                    <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-400">
                      {formatDateTime(incident.created_at)}
                    </td>

                    <td className="px-4 py-3">
                      <Link
                        to={`/incidents/${incident.id}`}
                        className="text-sm font-medium text-blue-400 hover:text-blue-300"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}