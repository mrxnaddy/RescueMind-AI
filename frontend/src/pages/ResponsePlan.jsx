import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  getIncident,
  getResponsePlans,
  generateResponsePlan,
  approveResponsePlan,
  rejectResponsePlan,
} from '../services/api'

export default function ResponsePlan() {
  const { incidentId } = useParams()

  const [incident, setIncident] = useState(null)
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState('')
  const [notes, setNotes] = useState('')

  const loadData = async () => {
    try {
      setLoading(true)
      setError('')

      const incidentData = await getIncident(incidentId)
      setIncident(incidentData)

      const plans = await getResponsePlans(incidentId)

      if (Array.isArray(plans)) {
        setPlan(plans[0] || null)
      } else {
        setPlan(plans || null)
      }
    } catch (err) {
      setError(
        err.userMessage || 'Could not load response planning data.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [incidentId])

  const generatePlan = async () => {
    try {
      setGenerating(true)
      setError('')

      const result = await generateResponsePlan(incidentId)
      setPlan(result)
    } catch (err) {
      setError(
        err.userMessage || 'Could not generate response plan.',
      )
    } finally {
      setGenerating(false)
    }
  }

  const approve = async () => {
    if (!plan?.id) return

    try {
      setActionLoading(true)
      setError('')

      const result = await approveResponsePlan(plan.id, {
        notes: notes || 'Approved by Command Center operator.',
      })

      setPlan(result)
      setNotes('')
    } catch (err) {
      setError(
        err.userMessage || 'Could not approve response plan.',
      )
    } finally {
      setActionLoading(false)
    }
  }

  const reject = async () => {
    if (!plan?.id) return

    try {
      setActionLoading(true)
      setError('')

      const result = await rejectResponsePlan(plan.id, {
        notes: notes || 'Rejected by Command Center operator.',
      })

      setPlan(result)
      setNotes('')
    } catch (err) {
      setError(
        err.userMessage || 'Could not reject response plan.',
      )
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="text-slate-400">
        Loading response plan...
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link
            to={`/incidents/${incidentId}`}
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            ← Back to Incident
          </Link>

          <h1 className="mt-3 text-2xl font-bold text-white">
            Response Planning
          </h1>

          <p className="mt-1 text-sm text-slate-400">
            AI-assisted response recommendation for{' '}
            <span className="font-mono text-slate-300">
              {incident?.incident_code}
            </span>
          </p>
        </div>

        {plan && (
          <span
            className={[
              'rounded-full px-3 py-1 text-xs font-semibold',
              plan.status === 'approved'
                ? 'bg-green-500/15 text-green-300'
                : plan.status === 'rejected'
                  ? 'bg-red-500/15 text-red-300'
                  : 'bg-orange-500/15 text-orange-300',
            ].join(' ')}
          >
            {(plan.status || 'proposed').replaceAll('_', ' ')}
          </span>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Incident summary */}
      <section className="rounded-xl border border-navy-700 bg-navy-900 p-5">
        <h2 className="font-semibold text-white">
          Incident Summary
        </h2>

        <div className="mt-4 grid gap-4 md:grid-cols-4">
          <div>
            <div className="text-xs text-slate-500">Title</div>
            <div className="mt-1 text-sm text-slate-200">
              {incident?.title || '—'}
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Type</div>
            <div className="mt-1 text-sm capitalize text-slate-200">
              {incident?.emergency_type?.replaceAll('_', ' ') || '—'}
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Severity</div>
            <div className="mt-1 text-sm font-semibold uppercase text-orange-300">
              {incident?.severity || '—'}
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">Reports</div>
            <div className="mt-1 text-sm text-slate-200">
              {incident?.report_count ?? 0}
            </div>
          </div>
        </div>
      </section>

      {/* No plan */}
      {!plan && (
        <section className="rounded-xl border border-orange-500/30 bg-orange-500/5 p-8 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-orange-500/15 text-2xl">
            🤖
          </div>

          <h2 className="mt-4 text-xl font-semibold text-white">
            No Response Plan Yet
          </h2>

          <p className="mx-auto mt-2 max-w-lg text-sm text-slate-400">
            The Response Planning Agent can combine the incident
            information and produce a proposed response plan for
            human review.
          </p>

          <button
            type="button"
            onClick={generatePlan}
            disabled={generating}
            className="mt-6 rounded-lg bg-orange-600 px-6 py-3 text-sm font-semibold text-white hover:bg-orange-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {generating
              ? 'Generating AI Plan...'
              : 'Generate Response Plan'}
          </button>
        </section>
      )}

      {/* Plan */}
      {plan && (
        <>
          <section className="rounded-xl border border-blue-500/30 bg-blue-500/5 p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/15">
                🤖
              </div>

              <div>
                <h2 className="font-semibold text-white">
                  AI Proposed Response
                </h2>

                <p className="text-xs text-slate-400">
                  Generated by RescueMind Response Planning Agent
                </p>
              </div>
            </div>

            <div className="mt-5">
              <div className="text-xs font-semibold uppercase text-slate-500">
                Recommended Action
              </div>

              <div className="mt-2 rounded-lg bg-navy-950 p-4 text-sm leading-6 text-slate-200">
                {plan.recommended_action ||
                  plan.plan_text ||
                  plan.description ||
                  plan.response_plan ||
                  'No recommendation text available.'}
              </div>
            </div>
          </section>

          {/* Resources */}
          <section className="rounded-xl border border-navy-700 bg-navy-900 p-5">
            <h2 className="font-semibold text-white">
              Recommended Resources
            </h2>

            <div className="mt-4">
              {Array.isArray(plan.recommended_resources) &&
              plan.recommended_resources.length > 0 ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {plan.recommended_resources.map(
                    (resource, index) => (
                      <div
                        key={index}
                        className="rounded-lg border border-navy-700 bg-navy-950 p-4"
                      >
                        <div className="font-medium text-white">
                          {typeof resource === 'string'
                            ? resource
                            : resource.name ||
                              resource.resource_type ||
                              `Resource ${index + 1}`}
                        </div>

                        {typeof resource === 'object' &&
                          resource.reason && (
                            <div className="mt-1 text-xs text-slate-400">
                              {resource.reason}
                            </div>
                          )}
                      </div>
                    ),
                  )}
                </div>
              ) : (
                <div className="text-sm text-slate-400">
                  {plan.recommended_resources ||
                    plan.resources ||
                    'No specific resources listed.'}
                </div>
              )}
            </div>
          </section>

          {/* Reasoning */}
          {(plan.reasoning ||
            plan.rationale ||
            plan.explanation ||
            plan.missing_information) && (
            <section className="rounded-xl border border-navy-700 bg-navy-900 p-5">
              <h2 className="font-semibold text-white">
                AI Explainability
              </h2>

              {(plan.reasoning || plan.rationale || plan.explanation) && (
                <div className="mt-4">
                  <div className="text-xs uppercase text-slate-500">
                    Why this recommendation?
                  </div>

                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-300">
                    {plan.reasoning ||
                      plan.rationale ||
                      plan.explanation}
                  </p>
                </div>
              )}

              {plan.missing_information && (
                <div className="mt-4 rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-4">
                  <div className="text-xs uppercase text-yellow-400">
                    Missing Information
                  </div>

                  <p className="mt-2 text-sm text-yellow-200">
                    {Array.isArray(plan.missing_information)
                      ? plan.missing_information.join(', ')
                      : plan.missing_information}
                  </p>
                </div>
              )}
            </section>
          )}

          {/* Human approval */}
          {(plan.status === 'proposed' ||
            plan.status === 'pending') && (
            <section className="rounded-xl border border-orange-500/30 bg-navy-900 p-5">
              <div>
                <h2 className="font-semibold text-white">
                  Human Approval Required
                </h2>

                <p className="mt-1 text-sm text-slate-400">
                  Review the AI recommendation before taking any
                  operational action.
                </p>
              </div>

              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                rows={3}
                placeholder="Optional reviewer notes..."
                className="mt-4 w-full rounded-lg border border-navy-700 bg-navy-950 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
              />

              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={reject}
                  disabled={actionLoading}
                  className="rounded-lg border border-red-500/40 px-5 py-2.5 text-sm font-semibold text-red-300 hover:bg-red-500/10 disabled:opacity-50"
                >
                  {actionLoading ? 'Processing...' : 'Reject Plan'}
                </button>

                <button
                  type="button"
                  onClick={approve}
                  disabled={actionLoading}
                  className="rounded-lg bg-green-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-green-500 disabled:opacity-50"
                >
                  {actionLoading ? 'Processing...' : 'Approve Plan'}
                </button>
              </div>
            </section>
          )}

          {/* Final status */}
          {plan.status === 'approved' && (
            <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-5">
              <div className="text-lg font-semibold text-green-300">
                ✓ Response Plan Approved
              </div>

              <p className="mt-1 text-sm text-green-200/80">
                The proposed plan has received human approval.
              </p>
            </div>
          )}

          {plan.status === 'rejected' && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-5">
              <div className="text-lg font-semibold text-red-300">
                Response Plan Rejected
              </div>

              <p className="mt-1 text-sm text-red-200/80">
                The proposed AI plan was rejected by the operator.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}