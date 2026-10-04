import { useMemo, useState } from 'react'
import { useApi } from '../hooks/useApi'
import { getResources, getResourceSummary } from '../services/api'

export default function Resources() {
  const [type, setType] = useState('')
  const [status, setStatus] = useState('')
  const [availableOnly, setAvailableOnly] = useState(false)

  const params = useMemo(
    () => ({
      limit: 200,
      ...(type ? { resource_type: type } : {}),
      ...(status ? { status } : {}),
      ...(availableOnly ? { available_only: true } : {}),
    }),
    [type, status, availableOnly],
  )

  const resources = useApi(
    () => getResources(params),
    { intervalMs: 10000 },
  )

  const summary = useApi(
    getResourceSummary,
    { intervalMs: 10000 },
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">
          Resources
        </h1>
        <p className="text-sm text-slate-400">
          Simulated emergency resources and availability.
        </p>
      </div>

      {summary.data && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="rounded-xl border border-navy-700 bg-navy-900 p-4">
            <p className="text-xs text-slate-400">Total</p>
            <p className="mt-1 text-2xl font-bold text-white">
              {summary.data.total ?? 0}
            </p>
          </div>

          <div className="rounded-xl border border-navy-700 bg-navy-900 p-4">
            <p className="text-xs text-slate-400">Available</p>
            <p className="mt-1 text-2xl font-bold text-green-400">
              {summary.data.available ?? 0}
            </p>
          </div>

          <div className="rounded-xl border border-navy-700 bg-navy-900 p-4">
            <p className="text-xs text-slate-400">Assigned</p>
            <p className="mt-1 text-2xl font-bold text-orange-400">
              {summary.data.assigned ?? 0}
            </p>
          </div>

          <div className="rounded-xl border border-navy-700 bg-navy-900 p-4">
            <p className="text-xs text-slate-400">Unavailable</p>
            <p className="mt-1 text-2xl font-bold text-red-400">
              {summary.data.unavailable ?? 0}
            </p>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-navy-700 bg-navy-900 p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="mb-1 block text-xs text-slate-400">
              Resource type
            </label>

            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="rounded-lg border border-navy-700 bg-navy-950 px-3 py-2 text-sm text-white"
            >
              <option value="">All types</option>
              <option value="ambulance">Ambulance</option>
              <option value="rescue_team">Rescue team</option>
              <option value="fire_truck">Fire truck</option>
              <option value="medical_team">Medical team</option>
              <option value="shelter">Shelter</option>
              <option value="water">Water</option>
              <option value="food">Food</option>
              <option value="equipment">Equipment</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs text-slate-400">
              Status
            </label>

            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="rounded-lg border border-navy-700 bg-navy-950 px-3 py-2 text-sm text-white"
            >
              <option value="">All statuses</option>
              <option value="available">Available</option>
              <option value="assigned">Assigned</option>
              <option value="unavailable">Unavailable</option>
            </select>
          </div>

          <label className="flex items-center gap-2 pb-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={availableOnly}
              onChange={(e) => setAvailableOnly(e.target.checked)}
            />
            Available only
          </label>
        </div>
      </div>

      {resources.error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-300">
          Could not load resources: {resources.error.userMessage}
        </div>
      )}

      {resources.loading && !resources.data && (
        <div className="text-slate-400">
          Loading resources...
        </div>
      )}

      {resources.data && resources.data.length === 0 && (
        <div className="rounded-xl border border-navy-700 bg-navy-900 p-8 text-center text-slate-400">
          No resources found.
        </div>
      )}

      {resources.data && resources.data.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-navy-700 bg-navy-900">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-navy-700 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Quantity</th>
                  <th className="px-4 py-3">Location</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-navy-700">
                {resources.data.map((resource) => (
                  <tr
                    key={resource.id}
                    className="hover:bg-navy-800/50"
                  >
                    <td className="px-4 py-3 font-medium text-white">
                      {resource.name}
                    </td>

                    <td className="px-4 py-3 text-slate-300">
                      {resource.resource_type?.replaceAll('_', ' ')}
                    </td>

                    <td className="px-4 py-3">
                      <span
                        className={[
                          'rounded-full px-2 py-1 text-xs font-medium',
                          resource.status === 'available'
                            ? 'bg-green-500/15 text-green-300'
                            : resource.status === 'assigned'
                              ? 'bg-orange-500/15 text-orange-300'
                              : 'bg-red-500/15 text-red-300',
                        ].join(' ')}
                      >
                        {resource.status}
                      </span>
                    </td>

                    <td className="px-4 py-3 text-slate-300">
                      {resource.quantity ?? 0}
                    </td>

                    <td className="px-4 py-3 text-slate-400">
                      {resource.location_name || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="rounded-lg border border-orange-500/20 bg-orange-500/5 p-4 text-xs text-orange-300">
        Prototype data. Resource availability is simulated for the
        RescueMind AI demonstration.
      </div>
    </div>
  )
}