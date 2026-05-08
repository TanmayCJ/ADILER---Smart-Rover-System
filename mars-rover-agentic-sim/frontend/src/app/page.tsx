"use client";

import { useEffect, useMemo, useState } from "react";

import AgentCards from "@/components/AgentCards";
import ComparisonSection from "@/components/ComparisonSection";
import ScenarioSelector from "@/components/ScenarioSelector";
import ThreePanel from "@/components/ThreePanel";
import Timeline from "@/components/Timeline";
import {
	DemoReport,
	ScenarioResult,
	parseDemoReport,
} from "@/lib/demoData";

const DEFAULT_SCENARIOS = [
	"easy_navigation",
	"high_wind_navigation",
	"dust_storm_escape",
	"rocky_terrain",
	"energy_critical_route",
];

export default function HomePage() {
	const [report, setReport] = useState<DemoReport | null>(null);
	const [selectedScenario, setSelectedScenario] = useState<string>(
		DEFAULT_SCENARIOS[0]
	);

	useEffect(() => {
		let cancelled = false;
		fetch("/mock/demo_agent_run.json")
			.then((res) => res.json())
			.then((data) => {
				if (!cancelled) {
					setReport(parseDemoReport(data));
				}
			})
			.catch((error) => {
				console.error("Failed to load demo report", error);
			});
		return () => {
			cancelled = true;
		};
	}, []);

	const scenarios = report?.scenarios ?? [];
	const activeScenario = useMemo<ScenarioResult | null>(() => {
		return scenarios.find((scenario) => scenario.scenario_id === selectedScenario) ?? null;
	}, [scenarios, selectedScenario]);

	return (
		<main className="mx-auto flex min-h-screen max-w-7xl flex-col gap-8 px-6 py-10">
			<header className="flex flex-col gap-4">
				<div className="flex items-center justify-between">
					<div>
						<span className="badge">Mars Mission Control</span>
						<h1 className="mt-4 text-4xl font-semibold tracking-tight text-white">
							LangGraph Rover Demo Dashboard
						</h1>
						<p className="mt-2 max-w-2xl text-sm text-slate-300">
							Real-time style visualization of the multi-agent decision pipeline.
							Data is sourced from static demo reports for presentation use.
						</p>
					</div>
					<div className="hidden lg:block text-right text-xs text-slate-400">
						<p className="font-mono">Data source: reports/demo_agent_run.json</p>
						<p className="font-mono">Mode: offline replay</p>
					</div>
				</div>
			</header>

			<section className="panel p-6">
				<div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
					<div>
						<h2 className="text-xl font-semibold text-white">Scenario Selector</h2>
						<p className="text-sm text-slate-400">
							Switch scenarios to inspect environment inputs, planner decisions, and rover movement.
						</p>
					</div>
					<ScenarioSelector
						scenarios={DEFAULT_SCENARIOS}
						selected={selectedScenario}
						onSelect={setSelectedScenario}
					/>
				</div>
			</section>

			<section className="grid gap-6 lg:grid-cols-[1.35fr_1fr]">
				<div className="panel p-5">
					<div className="flex items-center justify-between">
						<h2 className="text-lg font-semibold text-white">3D Simulation Panel</h2>
						<span className="text-xs text-slate-400">Synthetic terrain view</span>
					</div>
					<div className="mt-4 h-[360px]">
						<ThreePanel scenario={activeScenario} />
					</div>
					<p className="mt-3 text-xs text-slate-400">
						Terrain shading reflects overall risk score. Obstacles are represented by synthetic markers
						derived from the hazard count.
					</p>
				</div>

				<div className="panel p-5">
					<h2 className="text-lg font-semibold text-white">Agent Workflow Timeline</h2>
					<p className="text-xs text-slate-400">
						Sequential view of the LangGraph agent execution loop.
					</p>
					<Timeline />
				</div>
			</section>

			<section className="panel p-6">
				<h2 className="text-lg font-semibold text-white">Agent Output Panel</h2>
				<p className="text-xs text-slate-400">
					Environment, planner, navigation, and memory outputs for the selected scenario.
				</p>
				<AgentCards scenario={activeScenario} />
			</section>

			<section className="panel p-6">
				<h2 className="text-lg font-semibold text-white">Scenario Comparison</h2>
				<p className="text-xs text-slate-400">
					Cross-scenario telemetry comparing risk, wind, dust, and obstacle density.
				</p>
				<ComparisonSection scenarios={scenarios} />
			</section>
		</main>
	);
}
