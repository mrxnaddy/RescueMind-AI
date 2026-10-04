export default function ComingSoon({ title, description }) {
  return (
    <div className="mx-auto max-w-xl rounded-xl border border-navy-700 bg-navy-900 p-8 text-center">
      <h1 className="text-2xl font-bold text-white">{title}</h1>
      <p className="mt-3 text-slate-400">{description}</p>
    </div>
  )
}