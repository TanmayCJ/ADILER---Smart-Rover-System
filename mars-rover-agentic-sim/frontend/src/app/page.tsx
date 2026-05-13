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
	const [playbackMode, setPlaybackMode] = useState<"interactive" | "cinematic">("interactive");
	const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
	const [audioEnabled, setAudioEnabled] = useState<boolean>(false);
	const [missionEvents, setMissionEvents] = useState<string[]>([]);
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
	const timelineProgress = useMemo(() => {
		if (phaseIndex < 0) return 0;
		const phaseValue = phaseIndex === 2 ? 2 + roverProgress : Math.min(phaseIndex, 4);
		return Math.min(phaseValue / (REPLAY_PHASES.length - 1), 1);
	}, [phaseIndex, roverProgress]);
	const analytics = useMemo(() => {
		const total = scenarios.length;
		if (total === 0) {
			return {
				total: 0,
				averageRisk: 0,
				highestRisk: null,
				safest: null,
				mostObstacles: null,
				strongestWind: null,
			};
		}
		let riskSum = 0;
		let highestRisk = scenarios[0];
		let safest = scenarios[0];
		let mostObstacles = scenarios[0];
		let strongestWind = scenarios[0];
		scenarios.forEach((scenario) => {
			const risk = scenario.environment?.risk_score ?? 0;
			const obstacles = scenario.environment?.obstacle_count ?? 0;
			const wind = scenario.environment?.wind_speed ?? 0;
			riskSum += risk;
			if (risk > (highestRisk.environment?.risk_score ?? 0)) highestRisk = scenario;
			if (risk < (safest.environment?.risk_score ?? 0)) safest = scenario;
			if (obstacles > (mostObstacles.environment?.obstacle_count ?? 0)) mostObstacles = scenario;
			if (wind > (strongestWind.environment?.wind_speed ?? 0)) strongestWind = scenario;
		});
		return {
			total,
			averageRisk: riskSum / total,
			highestRisk,
			safest,
			mostObstacles,
			strongestWind,
		};
	}, [scenarios]);

	const scenarioInsights = useMemo(() => {
		if (!activeScenario) return [] as string[];
		const insights: string[] = [];
		const action = activeScenario.planner?.action ?? "proceed";
		const env = activeScenario.environment;
		const wind = env?.wind_speed ?? 0;
		const dust = env?.dust_level ?? 0;
		const obstacles = env?.obstacle_count ?? 0;
		const risk = env?.risk_score ?? 0;
		const isEnergyCritical = activeScenario.scenario_id?.includes("energy_critical") ?? false;
		if (action === "reduce_speed") {
			insights.push("High wind conditions caused reduced-speed traversal.");
		}
		if (action === "hold_position") {
			insights.push("Dust storm risk triggered hold-position behavior.");
		}
		if (obstacles >= 8) {
			insights.push("Obstacle density forced cautious navigation.");
		}
		if (wind >= 12 && action !== "reduce_speed") {
			insights.push("Strong winds required tighter heading corrections.");
		}
		if (dust >= 0.6 && action !== "hold_position") {
			insights.push("Dust-heavy conditions reduced visibility and speed.");
		}
		if (risk >= 0.65) {
			insights.push("Elevated risk required conservative planning.");
		}
		if (isEnergyCritical) {
			insights.push("Energy-critical conditions limited rover progression.");
		}
		if (insights.length === 0) {
			insights.push("Nominal conditions supported steady navigation.");
		}
		return insights;
	}, [activeScenario]);

	const missionOutcome = useMemo(() => {
		if (!activeScenario) return "Mission Pending";
		if (phaseIndex < 0) return "Mission Pending";
		if (phaseIndex < 4) return "Mission In Progress";
		const action = activeScenario.planner?.action ?? "proceed";
		const isEnergyCritical = activeScenario.scenario_id?.includes("energy_critical") ?? false;
		if (isEnergyCritical) return "Mission Energy Constrained";
		if (action === "hold_position") return "Mission Paused";
		if (action === "reduce_speed") return "Mission Delayed";
		return "Mission Successful";
	}, [activeScenario, phaseIndex]);

	const averageRiskTone = analytics.averageRisk <= 0.35
		? "text-emerald-300"
		: analytics.averageRisk <= 0.6
			? "text-amber-300"
			: "text-red-300";
	const activeRiskTone = (activeScenario?.environment?.risk_score ?? 0) <= 0.35
		? "text-emerald-300"
		: (activeScenario?.environment?.risk_score ?? 0) <= 0.6
			? "text-amber-300"
			: "text-red-300";

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
		setMissionEvents([]);
		setReplayLog(activeScenario ? [
			`Scenario ready: ${activeScenario.scenario_id.replace(/_/g, " ")}`,
		] : []);
	};

	const appendMissionEvent = (entry: string) => {
		setMissionEvents((prev) => [...prev, entry].slice(-30));
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
		appendMissionEvent("Playback initiated.");
		setReplayLog([
			`Replay started: ${activeScenario.scenario_id.replace(/_/g, " ")}`,
			"Environment analysis completed.",
		]);
		const speedFactor = playbackSpeed || 1;
		const scaleDelay = (value: number) => value / speedFactor;
		const plannerAction = activeScenario.planner?.action ?? "proceed";
		const actionEventMessage =
			plannerAction === "reduce_speed"
				? "High wind detected. Navigation speed reduced."
				: plannerAction === "hold_position"
					? "Unsafe dust conditions detected. Rover holding position."
					: plannerAction === "conserve_energy"
						? "Energy-critical route detected. Conserving traversal power."
						: plannerAction === "proceed_cautious"
							? "Moderate hazard profile detected. Proceeding cautiously."
							: "Low-risk path confirmed. Proceeding toward goal.";

		const scheduleStep = (
			index: number,
			delayMs: number,
			logMessage: string,
			eventMessage?: string
		) => {
			const timeoutId = window.setTimeout(() => {
				setPhaseIndex(index);
				setReplayLog((prev) => [...prev, logMessage]);
				if (eventMessage) {
					appendMissionEvent(eventMessage);
				}
				if (index === 2) {
					animateRover(scaleDelay(5200));
				}
				if (index === 4) {
					setIsReplaying(false);
				}
			}, scaleDelay(delayMs));
			timeoutsRef.current.push(timeoutId);
		};

		scheduleStep(1, 1600, "Planning decision recorded.", actionEventMessage);
		scheduleStep(2, 3600, "Navigation executed: rover advancing toward goal.", "Navigation rerouting initiated.");
		scheduleStep(3, 9800, "Memory update written.", "Memory event stored.");
		scheduleStep(4, 12800, "Final verdict issued.", "Mission complete.");
	};

	const jumpToPhase = (index: number) => {
		setPhaseIndex(index);
		if (index < 2) {
			setRoverProgress(0);
		} else if (index === 2) {
			setRoverProgress(0.45);
		} else {
			setRoverProgress(1);
		}
		appendMissionEvent(`Jumped to ${REPLAY_PHASES[index]}.`);
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
								onClick={() => setPlaybackMode("interactive")}
								className={`rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.2em] transition ${
									playbackMode === "interactive"
										? "border-sky-300/70 bg-sky-500/20 text-sky-100"
										: "border-slate-700/70 bg-slate-900/60 text-slate-400"
								}`}
								disabled={isReplaying}
							>
								Interactive View
							</button>
							<button
								type="button"
								onClick={() => setPlaybackMode("cinematic")}
								className={`rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.2em] transition ${
									playbackMode === "cinematic"
										? "border-amber-300/70 bg-amber-500/20 text-amber-100"
										: "border-slate-700/70 bg-slate-900/60 text-slate-400"
								}`}
								disabled={isReplaying}
							>
								Cinematic Playback
							</button>
						</div>
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
						<div className="flex flex-wrap items-center gap-2">
							<div className="flex items-center gap-2 rounded-full border border-slate-700/70 bg-slate-950/60 px-3 py-1">
								<span className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Speed</span>
								{[0.5, 1, 2].map((speed) => (
									<button
										key={speed}
										type="button"
										onClick={() => setPlaybackSpeed(speed)}
										disabled={isReplaying}
										className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-[0.2em] transition ${
											playbackSpeed === speed
												? "bg-slate-200/10 text-slate-100"
												: "text-slate-500"
										}`}
									>
										{speed}x
									</button>
								))}
							</div>
							<button
								type="button"
								onClick={() => setAudioEnabled((prev) => !prev)}
								className={`flex items-center gap-2 rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.2em] transition ${
									audioEnabled
										? "border-emerald-300/60 bg-emerald-500/20 text-emerald-100"
										: "border-slate-700/70 bg-slate-900/60 text-slate-400"
								}`}
							>
								<svg
									aria-hidden
									viewBox="0 0 24 24"
									className="h-3 w-3"
									fill="none"
									stroke="currentColor"
									strokeWidth="1.6"
								>
									<path d="M4 10h4l5-4v12l-5-4H4z" />
									<path d="M17 9c1.3 1 1.3 5 0 6" />
								</svg>
								{audioEnabled ? "Audio On" : "Audio Off"}
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
							cinematicMode={playbackMode === "cinematic"}
						/>
					</div>
					<div className="mt-4 rounded-xl border border-slate-700/60 bg-slate-950/40 p-3">
						<div className="flex items-center justify-between text-[10px] uppercase tracking-[0.2em] text-slate-400">
							<span>Mission Playback</span>
							<span>{phaseLabel}</span>
						</div>
						<div className="mt-3 grid grid-cols-5 gap-2 text-[10px]">
							{REPLAY_PHASES.map((phase, index) => {
								const isActive = index === phaseIndex;
								const isComplete = phaseIndex >= 0 && index < phaseIndex;
								return (
									<button
										key={phase}
										type="button"
										onClick={() => jumpToPhase(index)}
										className={`rounded-lg border px-2 py-1 text-center uppercase tracking-[0.18em] transition ${
											isActive
												? "border-orange-400/60 bg-orange-500/15 text-orange-100"
												: isComplete
													? "border-slate-600/60 bg-slate-900/60 text-slate-200"
													: "border-slate-800/60 bg-slate-950/60 text-slate-500"
										}`}
									>
										{phase.split(" ")[0]}
									</button>
								);
							})}
						</div>
						<div className="mt-3 h-1 w-full rounded-full bg-slate-900/80">
							<div
								className="h-1 rounded-full bg-orange-400/80 transition-all duration-500"
								style={{ width: `${timelineProgress * 100}%` }}
							/>
						</div>
					</div>
					<div className="mt-4 rounded-xl border border-slate-700/60 bg-slate-950/40 p-4">
						<h3 className="text-xs uppercase tracking-[0.2em] text-slate-400">Mission Event Feed</h3>
						<ul className="mt-3 max-h-32 space-y-2 overflow-y-auto text-xs text-slate-300">
							{missionEvents.length === 0 ? (
								<li>Awaiting replay events.</li>
							) : (
								missionEvents.map((entry, index) => (
									<li key={`${entry}-${index}`} className="border-b border-slate-800/60 pb-2 last:border-b-0">
										{entry}
									</li>
								))
							)}
						</ul>
					</div>
					<div className="mt-4 rounded-xl border border-slate-700/60 bg-slate-950/40 p-4">
						<h3 className="text-xs uppercase tracking-[0.2em] text-slate-400">Demo Ready</h3>
						<div className="mt-3 grid gap-2 text-xs text-slate-300">
							<div className="flex items-center justify-between">
								<span>LangGraph workflow</span>
								<span className="text-emerald-300">Active</span>
							</div>
							<div className="flex items-center justify-between">
								<span>Scenario validation</span>
								<span className="text-emerald-300">Passed</span>
							</div>
							<div className="flex items-center justify-between">
								<span>Replay system</span>
								<span className="text-emerald-300">Synced</span>
							</div>
							<div className="flex items-center justify-between">
								<span>Memory event</span>
								<span className="text-emerald-300">Recorded</span>
							</div>
						</div>
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
				<div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
					<div>
						<h2 className="text-lg font-semibold text-white">Mission Analytics</h2>
						<p className="text-xs text-slate-400">
							Scenario-level analytics and mission-control insights.
						</p>
					</div>
					<div className="rounded-full border border-slate-700/70 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-300">
						{missionOutcome}
					</div>
				</div>
				<div className="mt-5 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
					<div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
						<div className="rounded-xl border border-slate-700/60 bg-slate-950/60 p-4">
							<p className="text-xs uppercase tracking-[0.2em] text-slate-400">Total Scenarios</p>
							<p className="mt-2 text-2xl font-semibold text-white">{analytics.total}</p>
						</div>
						<div className="rounded-xl border border-slate-700/60 bg-slate-950/60 p-4">
							<p className="text-xs uppercase tracking-[0.2em] text-slate-400">Average Risk</p>
							<p className={`mt-2 text-2xl font-semibold ${averageRiskTone}`}>
								{analytics.averageRisk.toFixed(2)}
							</p>
						</div>
						<div className="rounded-xl border border-slate-700/60 bg-slate-950/60 p-4">
							<p className="text-xs uppercase tracking-[0.2em] text-slate-400">Highest Risk</p>
							<p className="mt-2 text-sm font-semibold text-white">
								{analytics.highestRisk?.scenario_id ?? "Unknown"}
							</p>
							<p className="text-xs text-slate-400">
								Risk {(analytics.highestRisk?.environment?.risk_score ?? 0).toFixed(2)}
							</p>
						</div>
						<div className="rounded-xl border border-slate-700/60 bg-slate-950/60 p-4">
							<p className="text-xs uppercase tracking-[0.2em] text-slate-400">Safest Scenario</p>
							<p className="mt-2 text-sm font-semibold text-white">
								{analytics.safest?.scenario_id ?? "Unknown"}
							</p>
							<p className="text-xs text-slate-400">
								Risk {(analytics.safest?.environment?.risk_score ?? 0).toFixed(2)}
							</p>
						</div>
						<div className="rounded-xl border border-slate-700/60 bg-slate-950/60 p-4">
							<p className="text-xs uppercase tracking-[0.2em] text-slate-400">Most Obstacles</p>
							<p className="mt-2 text-sm font-semibold text-white">
								{analytics.mostObstacles?.scenario_id ?? "Unknown"}
							</p>
							<p className="text-xs text-slate-400">
								{analytics.mostObstacles?.environment?.obstacle_count ?? 0} hazards
							</p>
						</div>
						<div className="rounded-xl border border-slate-700/60 bg-slate-950/60 p-4">
							<p className="text-xs uppercase tracking-[0.2em] text-slate-400">Strongest Wind</p>
							<p className="mt-2 text-sm font-semibold text-white">
								{analytics.strongestWind?.scenario_id ?? "Unknown"}
							</p>
							<p className="text-xs text-slate-400">
								{(analytics.strongestWind?.environment?.wind_speed ?? 0).toFixed(1)} m/s
							</p>
						</div>
					</div>
					<div className="space-y-4">
						<div className="rounded-xl border border-slate-700/60 bg-slate-950/60 p-4">
							<div className="flex items-center justify-between">
								<h3 className="text-xs uppercase tracking-[0.2em] text-slate-400">
									Scenario Insights
								</h3>
								<span className={`text-xs font-semibold ${activeRiskTone}`}>
									Risk {(activeScenario?.environment?.risk_score ?? 0).toFixed(2)}
								</span>
							</div>
							<ul className="mt-3 space-y-2 text-xs text-slate-300">
								{scenarioInsights.map((insight, index) => (
									<li key={`${insight}-${index}`}>
										{insight}
									</li>
								))}
							</ul>
						</div>
						<div className="rounded-xl border border-slate-700/60 bg-slate-950/60 p-4">
							<h3 className="text-xs uppercase tracking-[0.2em] text-slate-400">
								System Status
							</h3>
							<div className="mt-3 grid gap-2 text-xs text-slate-300">
								<div className="flex items-center justify-between">
									<span>LangGraph</span>
									<span className="text-emerald-300">Active</span>
								</div>
								<div className="flex items-center justify-between">
									<span>Replay Engine</span>
									<span className="text-emerald-300">Active</span>
								</div>
								<div className="flex items-center justify-between">
									<span>Telemetry</span>
									<span className="text-emerald-300">Synced</span>
								</div>
								<div className="flex items-center justify-between">
									<span>Memory Agent</span>
									<span className="text-emerald-300">Online</span>
								</div>
							</div>
						</div>
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
