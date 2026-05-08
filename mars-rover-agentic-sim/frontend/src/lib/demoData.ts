export type DemoReport = {
  scenarios: ScenarioResult[];
};

export type ScenarioResult = {
  scenario_id: string;
  status: string;
  failure_reason?: string;
  scenario_loaded?: {
    mission_id: string;
    start: string;
    goal: string;
    terrain_tile: string;
  };
  environment?: {
    risk_score: number;
    slope: number;
    roughness: number;
    wind_speed: number;
    dust_level: number;
    obstacle_count: number;
    risk_level: string;
  };
  planner?: {
    action: string;
    rationale: string;
  };
  navigation?: {
    initial_position: string;
    final_position: string;
    movement_step: string;
    status: string;
  };
  memory?: {
    events_written: number;
    latest_event: {
      risk_score?: number;
      action?: string;
      position?: { x: number; y: number; z?: number };
    } | null;
  };
  final_verdict?: string;
  distance_to_goal?: number;
};

export type ParsedPosition = { x: number; y: number };

export function parsePosition(value: string | undefined): ParsedPosition | null {
  if (!value) return null;
  const match = value.match(/-?\d+(?:\.\d+)?/g);
  if (!match || match.length < 2) return null;
  return { x: Number(match[0]), y: Number(match[1]) };
}

export function parseDemoReport(data: DemoReport): DemoReport {
  return {
    scenarios: Array.isArray(data.scenarios) ? data.scenarios : [],
  };
}
