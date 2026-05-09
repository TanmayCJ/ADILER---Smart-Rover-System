const steps = [
  "Environment Agent",
  "Planner Agent",
  "Navigation Agent",
  "Memory Agent",
];

type TimelineProps = {
  activeStep?: number;
};

export default function Timeline({ activeStep = -1 }: TimelineProps) {
  return (
    <div className="mt-6 flex flex-col gap-4">
      {steps.map((step, index) => {
        const isActive = index === activeStep;
        return (
          <div
            key={step}
            className={`flex items-center gap-4 rounded-xl border px-4 py-3 transition ${
              isActive
                ? "border-orange-400/60 bg-orange-500/10"
                : "border-slate-700/60 bg-slate-950/50"
            }`}
          >
            <span
              className={`flex h-9 w-9 items-center justify-center rounded-full border text-xs ${
                isActive
                  ? "border-orange-300 bg-orange-500/20 text-orange-100"
                  : "border-orange-400/40 bg-orange-500/10 text-orange-200"
              }`}
            >
              {index + 1}
            </span>
            <div>
              <p className="text-sm text-slate-100">{step}</p>
              <p className="text-xs text-slate-500">
                {isActive ? "Active phase in replay." : "Queued in the LangGraph flow."}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
