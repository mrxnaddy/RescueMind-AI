import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import HealthIndicator from '../components/HealthIndicator'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/map', label: 'Emergency Map' },
  { to: '/incidents', label: 'Incidents' },
  { to: '/resources', label: 'Resources' },
  { to: '/duplicates', label: 'Duplicate Review' },
  { to: '/ai-activity', label: 'AI Activity' },
  { to: '/report', label: 'Report Emergency' },
  { to: '/assignments', label: 'Assignments' },
]

function navClass({ isActive }) {
  return [
    'flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
    isActive
      ? 'bg-orange-500/15 text-orange-300 ring-1 ring-orange-500/30'
      : 'text-slate-300 hover:bg-navy-800 hover:text-white',
  ].join(' ')
}

export default function AppLayout() {
  const [open, setOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-navy-950">
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-navy-700 bg-navy-900 transition-transform md:static md:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="border-b border-navy-700 px-5 py-5">
          <div className="text-xl font-bold tracking-tight">
            <span className="text-orange-500">Rescue</span>
            <span className="text-white">Mind</span>{' '}
            <span className="text-red-500">AI</span>
          </div>
          <div className="mt-1 text-xs text-slate-400">
            Emergency Command Center
          </div>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={navClass}
              onClick={() => setOpen(false)}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-navy-700 p-4 text-xs text-slate-400">
          Prototype. All data is simulated. AI output is a suggestion; a human
          decides.
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-3 border-b border-navy-700 bg-navy-900/80 px-4 py-3">
          <button
            type="button"
            className="rounded-md p-2 text-slate-300 hover:bg-navy-800 md:hidden"
            onClick={() => setOpen(true)}
            aria-label="Open menu"
          >
            ☰
          </button>

          <span className="rounded-full bg-orange-500/15 px-3 py-1 text-xs font-semibold text-orange-300 ring-1 ring-orange-500/30">
            SIMULATED DATA - human approval required
          </span>

          <HealthIndicator />
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}