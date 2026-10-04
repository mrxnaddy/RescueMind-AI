import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { SeverityBadge, StatusBadge } from '../components/Badges'
import StatCard from '../components/StatCard'
import { useApi } from '../hooks/useApi'
import { getDashboardStats, getIncidents } from '../services/api'
import { SEVERITY_META, SEVERITY_ORDER } from '../utils/constants'
import { formatDateTime } from '../utils/format'

const fetchLatest = () => getIncidents({ limit: 6 })

export default function Dashboard() {
  const stats = useApi(getDashboardStats, { intervalMs: 10000 })
  const latest = useApi(fetchLatest, { intervalMs: 10000 })

  const chartData = SEVERITY_ORDER.map((level) => ({
    name: SEVERITY_META[level].label,
    count: stats.data?.active_by_severity?.[level] ?? 0,
    color: SEVERITY_META[level].color,
  }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Command Dashboard</h1>
        <p className="text-sm text-slate-400">
          Live numbers from the backend. Merged incidents are not counted.
        </p>
      </div>

      {stats.error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-300">
          Could not load the dashboard: {stats.error.userMessage}
        </div>
      )}

      {stats.loading && !stats.data && (
        <div className="text-slate-400">Loading...</div>
      )}

      {stats.data && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
          <StatCard label="Total" value={stats.data.total_incidents} />
          <StatCard label="Pending" value={stats.data.pending} />
          <StatCard label="Urgent" value={stats.data.urgent} accent="red" />
          <StatCard label="Assigned" value={stats.data.assigned} accent="orange" />
          <StatCard label="In progress" value={stats.data.in_progress} accent="orange" />
          <StatCard label="Resolved" value={stats.data.resolved} accent="green" />
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-xl border border-navy-700 bg-navy-900 p-4">
          <h2 className="mb-1 font-semibold text-white">Open incidents by severity</h2>
          <p className="mb-4 text-xs text-slate-400">
            AI severity estimates (not verified). Resolved and merged incidents are excluded.
          </p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#18264a" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis allowDecimals={false} stroke="#94a3b8" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: '#0a1226',
                    border: '1px solid #18264a',
                    color: '#e2e8f0',
                  }}
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="rounded-xl border border-navy-700 bg-navy-900 p-4">
          <h2 className="mb-4 font-semibold text-white">Latest incidents</h2>

          {latest.error && (
            <div className="text-sm text-red-300">
              Could not load incidents: {latest.error.userMessage}
            </div>
          )}

          {latest.data && latest.data.length === 0 && (
            <div className="text-sm text-slate-400">No incidents yet.</div>
          )}

          {latest.data && latest.data.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase text-slate-400">
                  <tr>
                    <th className="pb-2 pr-3">Code</th>
                    <th className="pb-2 pr-3">Title</th>
                    <th className="pb-2 pr-3">Severity</th>
                    <th className="pb-2 pr-3">Status</th>
                    <th className="pb-2">Reported</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-navy-700">
                  {latest.data.map((incident) => (
                    <tr key={incident.id}>
                      <td className="py-2 pr-3 font-mono text-xs text-slate-300">
                        {incident.incident_code}
                      </td>
                      <td className="max-w-[14rem] truncate py-2 pr-3 text-slate-200">
                        {incident.title}
                      </td>
                      <td className="py-2 pr-3">
                        <SeverityBadge severity={incident.severity} />
                      </td>
                      <td className="py-2 pr-3">
                        <StatusBadge status={incident.status} />
                      </td>
                      <td className="whitespace-nowrap py-2 text-xs text-slate-400">
                        {formatDateTime(incident.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}