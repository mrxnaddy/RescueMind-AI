import { useApi } from '../hooks/useApi'
import { getDatabaseHealth, getHealth } from '../services/api'

// Checks the API and the database.
async function checkBackend() {
  await getHealth()
  return getDatabaseHealth()
}

export default function HealthIndicator() {
  const { data, error, loading } = useApi(checkBackend, { intervalMs: 15000 })

  let dot = 'bg-slate-400'
  let text = 'Checking...'

  if (error) {
    dot = 'bg-red-500'
    text = 'API offline'
  } else if (!loading && data) {
    dot = 'bg-emerald-400'
    text = 'API online'
  }

  return (
    <div className="flex items-center gap-2 text-sm text-slate-300">
      <span className={`h-2.5 w-2.5 rounded-full ${dot}`} />
      {text}
    </div>
  )
}