import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../services/api'

const AGENTS = [
  'Intake Agent',
  'Location Intelligence',
  'Severity Assessment',
  'Duplicate Detection',
  'Resource Matching',
  'Response Planning',
]

function formatDate(value) {
  if (!value) return '—'

  try {
    return new Date(value).toLocaleString()
  } catch {
    return String(value)
  }
}

function prettyValue(value) {
  if (value === null || value === undefined || value === '') {
    return '—'
  }

  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }

  return String(value)
}

function statusClass(status) {
  const value = String(status || '').toLowerCase()

  if (
    value.includes('success') ||
    value.includes('completed') ||
    value.includes('approved')
  ) {
    return 'bg-green-500/15 text-green-300'
  }

  if (
    value.includes('fail') ||
    value.includes('error') ||
    value.includes('reject')
  ) {
    return 'bg-red-500/15 text-red-300'
  }

  if (
    value.includes('running') ||
    value.includes('process') ||
    value.includes('pending')
  ) {
    return 'bg-yellow-500/15 text-yellow-300'
  }

  return 'bg-slate-500/15 text-slate-300'
}

export default function AIActivity() {
  const [executions, setExecutions] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [expandedId, setExpandedId] = useState(null)

  const loadExecutions = useCallback(async (manual = false) => {
    try {
      if (manual) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      setError('')

      const response = await api.get('/api/agent-executions/')
      const data = response.data

      if (Array.isArray(data)) {
        setExecutions(data)
      } else {
        setExecutions(
          data?.executions ||
            data?.items ||
            data?.data ||
            [],
        )
      }
    } catch (err) {
      setError(
        err.userMessage ||
          err.response?.data?.detail ||
          'Could not load AI activity.',
      )
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadExecutions()

    const interval = setInterval(() => {
      loadExecutions()
    }, 10000)

    return () => clearInterval(interval)
  }, [loadExecutions])

  const stats = useMemo(() => {
    const total = executions.length

    const successful = executions.filter((item) => {
      const status = String(item.status || '').toLowerCase()

      return (
        status.includes('success') ||
        status.includes('completed')
      )
    }).length

    const failed = executions.filter((item) => {
      const status = String(item.status || '').toLowerCase()

      return (
        status.includes('fail') ||
        status.includes('error')
      )
    }).length

    const running = executions.filter((item) => {
      const status = String(item.status || '').toLowerCase()

      return (
        status.includes('running') ||
        status.includes('process') ||
        status.includes('pending')
      )
    }).length

    return {
      total,
      successful,
      failed,
      running,
    }
  }, [executions])

  const getAgentCount = (agentName) => {
    return executions.filter((item) => {
      const name = String(
        item.agent_name ||
          item.agent ||
          item.agent_type ||
          '',
      ).toLowerCase()

      return name.includes(agentName.toLowerCase())
    }).length
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">
            AI Activity
          </h1>

          <p className="mt-1 text-sm text-slate-400">
            Live agent execution and AI processing monitor.
          </p>
        </div>

        <button
          type="button"
          onClick={() => loadExecutions(true)}
          disabled={refreshing}
          className="rounded-lg border border-navy-700 bg-navy-900 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-navy-800 disabled:opacity-50"
        >
          {refreshing ? 'Refreshing...' : '↻ Refresh'}
        </button>
      </div>

      {/* Warning */}
      <div className="rounded-xl border border-orange-500/30 bg-orange-500/10 p-4 text-sm text-orange-300">
        AI output is advisory only. Emergency decisions require
        human approval.
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-navy-700 bg-navy-900 p-5">
          <div className="text-sm text-slate-400">
            Total Executions
          </div>

          <div className="mt-2 text-3xl font-bold text-white">
            {stats.total}
          </div>
        </div>

        <div className="rounded-xl border border-green-500/20 bg-navy-900 p-5">
          <div className="text-sm text-slate-400">
            Completed
          </div>

          <div className="mt-2 text-3xl font-bold text-green-300">
            {stats.successful}
          </div>
        </div>

        <div className="rounded-xl border border-yellow-500/20 bg-navy-900 p-5">
          <div className="text-sm text-slate-400">
            Running / Pending
          </div>

          <div className="mt-2 text-3xl font-bold text-yellow-300">
            {stats.running}
          </div>
        </div>

        <div className="rounded-xl border border-red-500/20 bg-navy-900 p-5">
          <div className="text-sm text-slate-400">
            Failed
          </div>

          <div className="mt-2 text-3xl font-bold text-red-300">
            {stats.failed}
          </div>
        </div>
      </div>

      {/* Agent cards */}
      <section>
        <div className="mb-3">
          <h2 className="text-lg font-semibold text-white">
            Agent Status
          </h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {AGENTS.map((agent) => {
            const count = getAgentCount(agent)

            return (
              <div
                key={agent}
                className="rounded-xl border border-navy-700 bg-navy-900 p-5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-white">
                      {agent}
                    </h3>

                    <p className="mt-1 text-xs text-slate-500">
                      Multi-agent emergency intelligence
                    </p>
                  </div>

                  <span className="rounded-full bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-300">
                    {count} runs
                  </span>
                </div>

                <div className="mt-4 flex items-center gap-2 text-xs text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-green-400" />
                  Execution tracking active
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* Execution log */}
      <section className="rounded-xl border border-navy-700 bg-navy-900">
        <div className="flex items-center justify-between border-b border-navy-700 p-5">
          <div>
            <h2 className="font-semibold text-white">
              Execution Log
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Latest agent processing activity
            </p>
          </div>

          <span className="text-xs text-slate-500">
            Auto-refresh: 10s
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-slate-400">
            Loading AI executions...
          </div>
        ) : executions.length === 0 ? (
          <div className="p-10 text-center">
            <div className="text-3xl">🤖</div>

            <div className="mt-3 font-semibold text-white">
              No AI executions yet
            </div>

            <p className="mt-1 text-sm text-slate-500">
              Agent executions will appear here when the analysis
              pipeline processes emergency reports.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-navy-700 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-5 py-3">Agent</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Incident</th>
                  <th className="px-5 py-3">Started</th>
                  <th className="px-5 py-3">Details</th>
                </tr>
              </thead>

              <tbody>
                {executions.map((execution, index) => {
                  const id =
                    execution.id ??
                    execution.execution_id ??
                    index

                  const agent =
                    execution.agent_name ||
                    execution.agent ||
                    execution.agent_type ||
                    'Unknown Agent'

                  const status =
                    execution.status || 'unknown'

                  const incident =
                    execution.incident_id ||
                    execution.incident ||
                    '—'

                  const started =
                    execution.started_at ||
                    execution.created_at ||
                    execution.started ||
                    null

                  const isExpanded =
                    expandedId === id

                  return (
                    <React.Fragment key={id}>
                      <tr className="border-b border-navy-800">
                        <td className="px-5 py-4 font-medium text-white">
                          {agent}
                        </td>

                        <td className="px-5 py-4">
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusClass(
                              status,
                            )}`}
                          >
                            {status}
                          </span>
                        </td>

                        <td className="px-5 py-4 text-slate-300">
                          {incident}
                        </td>

                        <td className="px-5 py-4 text-xs text-slate-400">
                          {formatDate(started)}
                        </td>

                        <td className="px-5 py-4">
                          <button
                            type="button"
                            onClick={() =>
                              setExpandedId(
                                isExpanded ? null : id,
                              )
                            }
                            className="text-xs font-semibold text-orange-400 hover:text-orange-300"
                          >
                            {isExpanded
                              ? 'Hide'
                              : 'View'}
                          </button>
                        </td>
                      </tr>

                      {isExpanded && (
                        <tr className="border-b border-navy-800 bg-navy-950">
                          <td
                            colSpan="5"
                            className="p-5"
                          >
                            <div className="grid gap-4 md:grid-cols-2">
                              {Object.entries(execution).map(
                                ([key, value]) => (
                                  <div
                                    key={key}
                                    className="rounded-lg border border-navy-800 p-3"
                                  >
                                    <div className="text-xs uppercase text-slate-500">
                                      {key.replaceAll(
                                        '_',
                                        ' ',
                                      )}
                                    </div>

                                    <pre className="mt-1 whitespace-pre-wrap break-words text-xs text-slate-300">
                                      {prettyValue(value)}
                                    </pre>
                                  </div>
                                ),
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}