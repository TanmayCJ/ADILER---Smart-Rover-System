import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ScenarioResult } from "@/lib/demoData";

const chartColors = {
  risk: "#ff8a3d",
  wind: "#58a6ff",
  dust: "#d946ef",
  obstacles: "#facc15",
};

type ComparisonSectionProps = {
  scenarios: ScenarioResult[];
};

export default function ComparisonSection({ scenarios }: ComparisonSectionProps) {
  const data = scenarios.map((scenario) => ({
    name: scenario.scenario_id.replace(/_/g, " "),
    risk: scenario.environment?.risk_score ?? 0,
    wind: scenario.environment?.wind_speed ?? 0,
    dust: scenario.environment?.dust_level ?? 0,
    obstacles: scenario.environment?.obstacle_count ?? 0,
    action: scenario.planner?.action ?? "-",
    status: scenario.status ?? "-",
  }));

  return (
    <div className="mt-6 grid gap-6 lg:grid-cols-2">
      <div className="rounded-2xl border border-slate-700/50 bg-slate-950/40 p-4">
        <h3 className="text-sm font-semibold text-white">Risk Score</h3>
        <div className="mt-4 h-40">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#1f2937" strokeDasharray="4 4" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#0b1118", border: "1px solid #334155", color: "#e2e8f0" }} />
              <Bar dataKey="risk" fill={chartColors.risk} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-700/50 bg-slate-950/40 p-4">
        <h3 className="text-sm font-semibold text-white">Wind Speed</h3>
        <div className="mt-4 h-40">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#1f2937" strokeDasharray="4 4" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#0b1118", border: "1px solid #334155", color: "#e2e8f0" }} />
              <Bar dataKey="wind" fill={chartColors.wind} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-700/50 bg-slate-950/40 p-4">
        <h3 className="text-sm font-semibold text-white">Dust Level</h3>
        <div className="mt-4 h-40">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#1f2937" strokeDasharray="4 4" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#0b1118", border: "1px solid #334155", color: "#e2e8f0" }} />
              <Bar dataKey="dust" fill={chartColors.dust} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-700/50 bg-slate-950/40 p-4">
        <h3 className="text-sm font-semibold text-white">Obstacle Count</h3>
        <div className="mt-4 h-40">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#1f2937" strokeDasharray="4 4" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#0b1118", border: "1px solid #334155", color: "#e2e8f0" }} />
              <Bar dataKey="obstacles" fill={chartColors.obstacles} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="lg:col-span-2 rounded-2xl border border-slate-700/50 bg-slate-950/40 p-4">
        <h3 className="text-sm font-semibold text-white">Scenario Comparison Table</h3>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="text-[11px] uppercase tracking-[0.2em] text-slate-500">
              <tr>
                <th className="pb-2">Scenario</th>
                <th className="pb-2">Risk</th>
                <th className="pb-2">Wind</th>
                <th className="pb-2">Dust</th>
                <th className="pb-2">Obstacles</th>
                <th className="pb-2">Action</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.name} className="border-t border-slate-800/60">
                  <td className="py-3 font-medium text-slate-100">{row.name}</td>
                  <td className="py-3">{row.risk}</td>
                  <td className="py-3">{row.wind}</td>
                  <td className="py-3">{row.dust}</td>
                  <td className="py-3">{row.obstacles}</td>
                  <td className="py-3">{row.action}</td>
                  <td className="py-3">
                    <span className={row.status === "passed" ? "text-emerald-300" : "text-rose-300"}>
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
