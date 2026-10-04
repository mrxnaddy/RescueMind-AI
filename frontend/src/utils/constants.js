export const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'unknown']

// "color" is used by charts and the map. "badge" is used by Tailwind.
export const SEVERITY_META = {
  critical: {
    label: 'Critical',
    color: '#ef4444',
    badge: 'bg-red-500/15 text-red-300 ring-red-500/40',
  },
  high: {
    label: 'High',
    color: '#f97316',
    badge: 'bg-orange-500/15 text-orange-300 ring-orange-500/40',
  },
  medium: {
    label: 'Medium',
    color: '#eab308',
    badge: 'bg-yellow-500/15 text-yellow-300 ring-yellow-500/40',
  },
  low: {
    label: 'Low',
    color: '#22c55e',
    badge: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/40',
  },
  unknown: {
    label: 'Unknown',
    color: '#94a3b8',
    badge: 'bg-slate-500/15 text-slate-300 ring-slate-500/40',
  },
}

export const STATUS_META = {
  pending: {
    label: 'Pending',
    badge: 'bg-slate-500/15 text-slate-200 ring-slate-400/40',
  },
  under_review: {
    label: 'Under Review',
    badge: 'bg-sky-500/15 text-sky-300 ring-sky-500/40',
  },
  approved: {
    label: 'Approved',
    badge: 'bg-indigo-500/15 text-indigo-300 ring-indigo-500/40',
  },
  assigned: {
    label: 'Assigned',
    badge: 'bg-violet-500/15 text-violet-300 ring-violet-500/40',
  },
  in_progress: {
    label: 'In Progress',
    badge: 'bg-orange-500/15 text-orange-300 ring-orange-500/40',
  },
  resolved: {
    label: 'Resolved',
    badge: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/40',
  },
  merged: {
    label: 'Merged',
    badge: 'bg-slate-600/20 text-slate-400 ring-slate-500/30',
  },
}