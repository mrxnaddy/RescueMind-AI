import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'

const INITIAL_FORM = {
  reporter_name: '',
  reporter_phone: '',
  emergency_type: 'flood',
  description: '',
  address: '',
  latitude: '',
  longitude: '',
}

const emergencyTypes = [
  'flood',
  'earthquake',
  'fire',
  'road_accident',
  'medical',
]

function formatType(value) {
  if (!value) return 'Unknown'

  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

export default function ReportEmergency() {
  const [form, setForm] = useState(INITIAL_FORM)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  function handleChange(event) {
    const { name, value } = event.target

    setForm((current) => ({
      ...current,
      [name]: value,
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()

    setLoading(true)
    setError('')
    setResult(null)

    try {
      // STEP 1: Create citizen emergency report
      const reportResponse = await api.post('/api/emergency-reports/', {
        reporter_name: form.reporter_name.trim(),
        reporter_phone: form.reporter_phone.trim() || null,
        emergency_type: form.emergency_type,
        description: form.description.trim(),
        address: form.address.trim() || null,
        latitude:
          form.latitude.trim() === ''
            ? null
            : Number(form.latitude),
        longitude:
          form.longitude.trim() === ''
            ? null
            : Number(form.longitude),
      })

      const report = reportResponse.data

      // STEP 2: Run complete AI analysis
      const analysisResponse = await api.post(
        `/api/analysis/reports/${report.id}/analyze`,
      )

      const analysis = analysisResponse.data

      setResult({
        report,
        analysis,
      })

      // Clear form after successful submission
      setForm(INITIAL_FORM)
    } catch (err) {
      const message =
        err.userMessage ||
        err.response?.data?.detail ||
        'Unable to submit and analyze the emergency report.'

      setError(
        typeof message === 'string'
          ? message
          : 'Unable to process the emergency report.',
      )
    } finally {
      setLoading(false)
    }
  }

  const analysis = result?.analysis
  const summary = analysis?.summary

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <div className="text-sm font-semibold uppercase tracking-wider text-orange-400">
          Citizen Reporting
        </div>

        <h1 className="mt-1 text-2xl font-bold text-white">
          Report Emergency
        </h1>

        <p className="mt-1 text-sm text-slate-400">
          Submit an emergency report and let RescueMind AI analyze it for
          command-center review.
        </p>
      </div>

      <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-4 text-sm text-yellow-200">
        <strong>SIMULATED DATA:</strong> This is a hackathon prototype.
        AI assessments are recommendations and require human verification
        before operational action.
      </div>

      <form
        onSubmit={handleSubmit}
        className="rounded-xl border border-navy-700 bg-navy-900 p-5 shadow-xl"
      >
        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Reporter Name
            </label>

            <input
              name="reporter_name"
              value={form.reporter_name}
              onChange={handleChange}
              required
              minLength={2}
              className="w-full rounded-lg border border-navy-700 bg-navy-950 px-3 py-2.5 text-white outline-none focus:border-orange-500"
              placeholder="Test Citizen"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Phone
            </label>

            <input
              name="reporter_phone"
              value={form.reporter_phone}
              onChange={handleChange}
              className="w-full rounded-lg border border-navy-700 bg-navy-950 px-3 py-2.5 text-white outline-none focus:border-orange-500"
              placeholder="+92..."
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Emergency Type
            </label>

            <select
              name="emergency_type"
              value={form.emergency_type}
              onChange={handleChange}
              className="w-full rounded-lg border border-navy-700 bg-navy-950 px-3 py-2.5 text-white outline-none focus:border-orange-500"
            >
              {emergencyTypes.map((type) => (
                <option key={type} value={type}>
                  {formatType(type)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Address / Area
            </label>

            <input
              name="address"
              value={form.address}
              onChange={handleChange}
              className="w-full rounded-lg border border-navy-700 bg-navy-950 px-3 py-2.5 text-white outline-none focus:border-orange-500"
              placeholder="Example: Islamabad, Sector F-8"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Latitude
            </label>

            <input
              name="latitude"
              value={form.latitude}
              onChange={handleChange}
              type="number"
              step="any"
              min="-90"
              max="90"
              className="w-full rounded-lg border border-navy-700 bg-navy-950 px-3 py-2.5 text-white outline-none focus:border-orange-500"
              placeholder="33.6844"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Longitude
            </label>

            <input
              name="longitude"
              value={form.longitude}
              onChange={handleChange}
              type="number"
              step="any"
              min="-180"
              max="180"
              className="w-full rounded-lg border border-navy-700 bg-navy-950 px-3 py-2.5 text-white outline-none focus:border-orange-500"
              placeholder="73.0479"
            />
          </div>

          <div className="md:col-span-2">
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Emergency Description
            </label>

            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              required
              minLength={10}
              rows={6}
              className="w-full resize-y rounded-lg border border-navy-700 bg-navy-950 px-3 py-2.5 text-white outline-none focus:border-orange-500"
              placeholder="Describe what happened, who may be affected, visible danger, injuries, flooding, blocked roads, etc."
            />
          </div>
        </div>

        {error && (
          <div className="mt-5 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="mt-6 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-orange-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-orange-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading
              ? 'Submitting + AI Analysis...'
              : 'Submit & Analyze with AI'}
          </button>
        </div>
      </form>

      {result && (
        <div className="space-y-5">
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-5">
            <div className="text-sm font-semibold uppercase tracking-wider text-emerald-400">
              AI Analysis Complete
            </div>

            <h2 className="mt-2 text-xl font-bold text-white">
              Report #{result.report.id} processed
            </h2>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div>
                <div className="text-xs text-slate-400">
                  Incident ID
                </div>
                <div className="font-semibold text-white">
                  {analysis?.incident_id ?? 'Not created'}
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-400">
                  Incident Code
                </div>
                <div className="font-semibold text-orange-300">
                  {analysis?.incident_code ?? 'Pending'}
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-400">
                  Pipeline Status
                </div>
                <div className="font-semibold text-white">
                  {analysis?.status || 'Unknown'}
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-400">
                  Emergency Type
                </div>
                <div className="font-semibold text-white">
                  {formatType(summary?.emergency_type)}
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-400">
                  AI Severity
                </div>
                <div className="font-semibold text-red-300">
                  {summary?.severity || 'Unknown'}
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-400">
                  Severity Score
                </div>
                <div className="font-semibold text-white">
                  {summary?.severity_score ?? 'N/A'}
                </div>
              </div>
            </div>
          </div>

          {summary?.missing_information?.length > 0 && (
            <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-5">
              <h3 className="font-semibold text-yellow-300">
                Missing Information
              </h3>

              <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-yellow-100">
                {summary.missing_information.map((item, index) => (
                  <li key={`${item}-${index}`}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {analysis?.duplicate_check && (
            <div className="rounded-xl border border-navy-700 bg-navy-900 p-5">
              <h3 className="font-semibold text-white">
                Duplicate Detection
              </h3>

              <div className="mt-2 text-sm text-slate-300">
                Status:{' '}
                <span className="font-semibold text-orange-300">
                  {analysis.duplicate_check.status || 'checked'}
                </span>
              </div>

              <p className="mt-2 text-xs text-slate-400">
                Potential duplicates require human review before merging.
              </p>
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            {analysis?.incident_id && (
              <Link
                to={`/incidents/${analysis.incident_id}`}
                className="rounded-lg bg-orange-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-orange-500"
              >
                View Incident
              </Link>
            )}

            <Link
              to="/map"
              className="rounded-lg border border-navy-600 bg-navy-800 px-5 py-2.5 text-sm font-semibold text-white hover:bg-navy-700"
            >
              View Emergency Map
            </Link>

            <Link
              to="/incidents"
              className="rounded-lg border border-navy-600 bg-navy-800 px-5 py-2.5 text-sm font-semibold text-white hover:bg-navy-700"
            >
              All Incidents
            </Link>
          </div>

          <div className="rounded-xl border border-orange-500/30 bg-orange-500/10 p-4 text-sm text-orange-200">
            <strong>Human approval required:</strong> AI analysis is advisory.
            No emergency resource is automatically dispatched from this
            workflow.
          </div>
        </div>
      )}
    </div>
  )
}