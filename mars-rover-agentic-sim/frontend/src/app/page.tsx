"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import AgentCards from "@/components/AgentCards";
import ComparisonSection from "@/components/ComparisonSection";
import ScenarioSelector from "@/components/ScenarioSelector";
import ThreePanel from "@/components/ThreePanel";
import AgentDecisionTrace from "@/components/AgentDecisionTrace";
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

const REPLAY_PHASES = [
	"Environment Analysis",
	"Planning",
	"Navigation",
	"Memory Update",
	"Complete",
];

export default function HomePage() {
	const [report, setReport] = useState<DemoReport | null>(null);
	const [selectedScenario, setSelectedScenario] = useState<string>(
		DEFAULT_SCENARIOS[0]
	);
	const [phaseIndex, setPhaseIndex] = useState<number>(-1);
	const [replayLog, setReplayLog] = useState<string[]>([]);
	const [isReplaying, setIsReplaying] = useState<boolean>(false);
	const [roverProgress, setRoverProgress] = useState<number>(0);
	const timeoutsRef = useRef<number[]>([]);
	const animationRef = useRef<number | null>(null);

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

	const phaseLabel = phaseIndex >= 0 ? REPLAY_PHASES[phaseIndex] : "Ready";

	const resetReplay = () => {
		timeoutsRef.current.forEach((timeoutId) => clearTimeout(timeoutId));
		timeoutsRef.current = [];
		if (animationRef.current !== null) {
			cancelAnimationFrame(animationRef.current);
			animationRef.current = null;
		}
		setIsReplaying(false);
		setPhaseIndex(-1);
		setRoverProgress(0);
		setReplayLog(activeScenario ? [
			`Scenario ready: ${activeScenario.scenario_id.replace(/_/g, " ")}`,
		] : []);
	};

	const animateRover = (durationMs: number) => {
		if (animationRef.current !== null) {
			cancelAnimationFrame(animationRef.current);
		}
		const start = performance.now();
		const step = (timestamp: number) => {
			const progress = Math.min((timestamp - start) / durationMs, 1);
			setRoverProgress(progress);
			if (progress < 1) {
				animationRef.current = requestAnimationFrame(step);
			}
		};
		animationRef.current = requestAnimationFrame(step);
	};

	const startReplay = () => {
		if (!activeScenario) return;
		resetReplay();
		setIsReplaying(true);
		setPhaseIndex(0);
		setReplayLog([
			`Replay started: ${activeScenario.scenario_id.replace(/_/g, " ")}`,
			"Environment analysis completed.",
		]);

		const scheduleStep = (index: number, delayMs: number, logMessage: string) => {
			const timeoutId = window.setTimeout(() => {
				setPhaseIndex(index);
				setReplayLog((prev) => [...prev, logMessage]);
				if (index === 2) {
					animateRover(5200);
				}
				if (index === 4) {
					setIsReplaying(false);
				}
			}, delayMs);
			timeoutsRef.current.push(timeoutId);
		};

		scheduleStep(1, 1600, "Planning decision recorded.");
		scheduleStep(2, 3600, "Navigation executed: rover advancing toward goal.");
		scheduleStep(3, 9800, "Memory update written.");
		scheduleStep(4, 12800, "Final verdict issued.");
	};

	useEffect(() => {
		resetReplay();
		return () => {
			resetReplay();
		};
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [selectedScenario]);

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
					<div className="flex flex-col items-start gap-3 lg:items-end">
						<ScenarioSelector
							scenarios={DEFAULT_SCENARIOS}
							selected={selectedScenario}
							onSelect={setSelectedScenario}
						/>
						<div className="flex flex-wrap gap-2">
							<button
								type="button"
								onClick={startReplay}
								className="rounded-full border border-orange-400/40 bg-orange-500/20 px-4 py-2 text-xs uppercase tracking-[0.2em] text-orange-200 transition hover:bg-orange-500/30"
								disabled={isReplaying}
							>
								Replay Mission
							</button>
							<button
								type="button"
								onClick={resetReplay}
								className="rounded-full border border-slate-600 bg-slate-900/50 px-4 py-2 text-xs uppercase tracking-[0.2em] text-slate-300 transition hover:border-slate-400"
							>
								Reset
							</button>
						</div>
					</div>
				</div>
			</section>

			<section className="grid gap-6 lg:grid-cols-[1.35fr_1fr]">
				<div className="panel p-5">
					<div className="flex items-center justify-between">
						<h2 className="text-lg font-semibold text-white">3D Simulation Panel</h2>
						<span className="rounded-full border border-slate-700 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-300">
							{phaseLabel}
						</span>
					</div>
					<div className="mt-4 h-[360px]">
						<ThreePanel
							scenario={activeScenario}
							roverProgress={roverProgress}
							activePhase={phaseIndex}
						/>
					</div>
					<p className="mt-3 text-xs text-slate-400">
						Terrain shading reflects overall risk score. Obstacles are represented by synthetic markers
						derived from the hazard count.
					</p>
					<AgentDecisionTrace scenario={activeScenario} activePhase={phaseIndex} />
				</div>

				<div className="panel p-5">
					<h2 className="text-lg font-semibold text-white">Agent Workflow Timeline</h2>
					<p className="text-xs text-slate-400">
						Sequential view of the LangGraph agent execution loop.
					</p>
					<Timeline activeStep={phaseIndex} />
					<div className="mt-6 rounded-xl border border-slate-700/60 bg-slate-950/40 p-4">
						<h3 className="text-xs uppercase tracking-[0.2em] text-slate-400">Execution Log</h3>
						<ul className="mt-3 space-y-2 text-xs text-slate-300">
							{replayLog.length === 0 ? (
								<li>Awaiting replay command.</li>
							) : (
								replayLog.map((entry, index) => (
									<li key={`${entry}-${index}`} className="border-b border-slate-800/60 pb-2 last:border-b-0">
										{entry}
									</li>
								))
							)}
						</ul>
					</div>
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
