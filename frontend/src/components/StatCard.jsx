const ACCENTS = {
  default: { box: 'border-navy-700 bg-navy-900', value: 'text-white' },
  red: { box: 'border-red-500/50 bg-red-500/5', value: 'text-red-300' },
  orange: { box: 'border-orange-500/40 bg-orange-500/5', value: 'text-orange-300' },
  green: { box: 'border-emerald-500/40 bg-emerald-500/5', value: 'text-emerald-300' },
}

export default function StatCard({ label, value, accent = 'default' }) {
  const style = ACCENTS[accent] ?? ACCENTS.default

  return (
    <div className={`rounded-xl border p-4 ${style.box}`}>
      <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className={`mt-2 text-3xl font-bold ${style.value}`}>{value}</div>
    </div>
  )
}