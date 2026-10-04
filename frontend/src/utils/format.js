// The backend sends UTC times without a timezone. Treat them as UTC.
export function formatDateTime(value) {
  if (!value) return '-'

  const text = /Z$|[+-]\d\d:?\d\d$/.test(value) ? value : `${value}Z`
  const date = new Date(text)

  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleString()
}