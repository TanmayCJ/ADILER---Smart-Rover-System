import { ScenarioResult } from "@/lib/demoData";

const emptyState = {
  label: "Awaiting data",
  value: "-",
};

type AgentCardsProps = {
  scenario: ScenarioResult | null;
};

export default function AgentCards({ scenario }: AgentCardsProps) {
  if (!scenario) {
    return (
      <div className="mt-6 text-sm text-slate-400">Loading scenario data...</div>
    );
  }

  if (scenario.status !== "passed") {
    return (
      <div className="mt-6 rounded-xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">
        Scenario failed: {scenario.failure_reason}
      </div>
    );
  }

  const environment = scenario.environment ?? emptyState;
  const planner = scenario.planner ?? emptyState;
  const navigation = scenario.navigation ?? emptyState;
  const memory = scenario.memory ?? emptyState;

  return (
    <div className="mt-6 grid gap-4 lg:grid-cols-2">
      <div className="rounded-2xl border border-slate-700/60 bg-slate-950/40 p-4">
        <h3 className="text-sm font-semibold text-orange-200">Environment Agent</h3>
        <dl className="mt-3 grid gap-2 text-xs text-slate-300">
          <div className="flex justify-between"><span>Risk Score</span><span>{environment.risk_score ?? "-"}</span></div>
          <div className="flex justify-between"><span>Slope</span><span>{environment.slope ?? "-"}</span></div>
          <div className="flex justify-between"><span>Roughness</span><span>{environment.roughness ?? "-"}</span></div>
          <div className="flex justify-between"><span>Wind Speed</span><span>{environment.wind_speed ?? "-"}</span></div>
          <div className="flex justify-between"><span>Dust Level</span><span>{environment.dust_level ?? "-"}</span></div>
          <div className="flex justify-between"><span>Obstacles</span><span>{environment.obstacle_count ?? "-"}</span></div>
          <div className="flex justify-between"><span>Risk Level</span><span>{environment.risk_level ?? "-"}</span></div>
        </dl>
      </div>

      <div className="rounded-2xl border border-slate-700/60 bg-slate-950/40 p-4">
        <h3 className="text-sm font-semibold text-orange-200">Planner Agent</h3>
        <dl className="mt-3 grid gap-2 text-xs text-slate-300">
          <div className="flex justify-between"><span>Selected Action</span><span>{planner.action ?? "-"}</span></div>
          <div className="flex flex-col gap-1">
            <span className="text-slate-400">Rationale</span>
            <span className="text-slate-200">{planner.rationale ?? "-"}</span>
          </div>
        </dl>
      </div>

      <div className="rounded-2xl border border-slate-700/60 bg-slate-950/40 p-4">
        <h3 className="text-sm font-semibold text-orange-200">Navigation Agent</h3>
        <dl className="mt-3 grid gap-2 text-xs text-slate-300">
          <div className="flex justify-between"><span>Initial Position</span><span>{navigation.initial_position ?? "-"}</span></div>
          <div className="flex justify-between"><span>Final Position</span><span>{navigation.final_position ?? "-"}</span></div>
          <div className="flex justify-between"><span>Movement Step</span><span>{navigation.movement_step ?? "-"}</span></div>
          <div className="flex justify-between"><span>Status</span><span>{navigation.status ?? "-"}</span></div>
        </dl>
      </div>

      <div className="rounded-2xl border border-slate-700/60 bg-slate-950/40 p-4">
        <h3 className="text-sm font-semibold text-orange-200">Memory Agent</h3>
        <dl className="mt-3 grid gap-2 text-xs text-slate-300">
          <div className="flex justify-between"><span>Events Written</span><span>{memory.events_written ?? "-"}</span></div>
          <div className="flex flex-col gap-1">
            <span className="text-slate-400">Latest Event</span>
            <span className="text-slate-200 break-words">
              {memory.latest_event ? JSON.stringify(memory.latest_event) : "-"}
            </span>
          </div>
        </dl>
      </div>
    </div>
  );
}
