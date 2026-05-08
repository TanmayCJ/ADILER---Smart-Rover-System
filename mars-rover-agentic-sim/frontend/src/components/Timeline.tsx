const steps = [
  "Environment Agent",
  "Planner Agent",
  "Navigation Agent",
  "Memory Agent",
];

export default function Timeline() {
  return (
    <div className="mt-6 flex flex-col gap-4">
      {steps.map((step, index) => (
        <div
          key={step}
          className="flex items-center gap-4 rounded-xl border border-slate-700/60 bg-slate-950/50 px-4 py-3"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full border border-orange-400/40 bg-orange-500/10 text-xs text-orange-200">
            {index + 1}
          </span>
          <div>
            <p className="text-sm text-slate-100">{step}</p>
            <p className="text-xs text-slate-500">Executing sequentially in the LangGraph flow.</p>
          </div>
        </div>
      ))}
    </div>
  );
}
