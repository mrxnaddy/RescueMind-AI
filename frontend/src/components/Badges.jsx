import { SEVERITY_META, STATUS_META } from '../utils/constants'

const BASE =
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset'

export function SeverityBadge({ severity }) {
  const meta = SEVERITY_META[severity] ?? SEVERITY_META.unknown

  return <span className={`${BASE} ${meta.badge}`}>{meta.label}</span>
}

export function StatusBadge({ status }) {
  const meta = STATUS_META[status]

  return (
    <span
      className={`${BASE} ${meta ? meta.badge : 'bg-slate-500/15 text-slate-300 ring-slate-500/40'}`}
    >
      {meta ? meta.label : status}
    </span>
  )
}