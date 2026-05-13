import { ScenarioResult } from "@/lib/demoData";

const phases = [
  "Environment Agent",
  "Planner Agent",
  "Navigation Agent",
  "Memory Agent",
];

type AgentDecisionTraceProps = {
  scenario: ScenarioResult | null;
  activePhase?: number;
};

const formatValue = (value: string | number | undefined | null) => {
  if (value === null || value === undefined || value === "") return "Unknown";
  return String(value);
};

export default function AgentDecisionTrace({
  scenario,
  activePhase = -1,
}: AgentDecisionTraceProps) {
  const riskScore = scenario?.environment?.risk_score;
  const wind = formatValue(scenario?.environment?.wind_speed);
  const dust = formatValue(scenario?.environment?.dust_level);
  const slope = formatValue(scenario?.environment?.slope);
  const roughness = formatValue(scenario?.environment?.roughness);
  const obstacles = formatValue(scenario?.environment?.obstacle_count);
  const action = formatValue(scenario?.planner?.action);
  const rationale = formatValue(scenario?.planner?.rationale);
  const start = formatValue(scenario?.navigation?.initial_position);
  const final = formatValue(scenario?.navigation?.final_position);
  const memoryRisk = formatValue(scenario?.memory?.latest_event?.risk_score ?? riskScore);
  const memoryAction = formatValue(scenario?.memory?.latest_event?.action ?? scenario?.planner?.action);
  const memoryPosition = formatValue(
    scenario?.memory?.latest_event?.position
      ? `(${scenario?.memory?.latest_event?.position?.x}, ${scenario?.memory?.latest_event?.position?.y})`
      : scenario?.navigation?.final_position
  );

  const sentences = [
    `Analyzed wind ${wind}, dust ${dust}, slope ${slope}, roughness ${roughness}, and obstacles ${obstacles}. Risk score: ${riskScore?.toFixed(2) ?? "0.00"}.`,
    `Selected action: ${action}. Reason: ${rationale}.`,
    `Moved rover from ${start} to ${final} using ${action} behavior.`,
    `Stored mission event with risk score ${memoryRisk}, action ${memoryAction}, and final position ${memoryPosition}.`,
  ];

  return (
    <div className="mt-4 rounded-xl border border-slate-700/60 bg-slate-950/50 p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs uppercase tracking-[0.2em] text-slate-300">
          Agent Decision Trace
        </h3>
        <span className="text-[10px] uppercase tracking-[0.18em] text-slate-500">
          {activePhase >= 0 ? "Replay Active" : "Standby"}
        </span>
      </div>
      <div className="mt-3 grid gap-2">
        {phases.map((phase, index) => {
          const isComplete = activePhase >= 0 && index < activePhase;
          const isActive = index === activePhase;
          const isFuture = activePhase < 0 || index > activePhase;
          const cardTone = isActive
            ? "border-orange-400/60 bg-orange-500/10 text-orange-100"
            : isComplete
              ? "border-slate-600/70 bg-slate-900/60 text-slate-200"
              : "border-slate-800/60 bg-slate-950/40 text-slate-500";
          return (
            <div
              key={phase}
              className={`rounded-lg border px-3 py-2 text-xs transition ${cardTone}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase tracking-[0.16em]">
                  {phase}
                </span>
                <span className="text-[10px] uppercase tracking-[0.2em] text-slate-400">
                  {isActive ? "Active" : isComplete ? "Done" : "Queued"}
                </span>
              </div>
              <p className="mt-2 text-[11px] text-slate-300">
                {sentences[index]}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
