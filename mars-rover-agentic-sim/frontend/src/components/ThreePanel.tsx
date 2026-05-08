import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useMemo } from "react";

import { ScenarioResult, parsePosition } from "@/lib/demoData";

const surfaceColors = ["#1f7a4a", "#bf6b2b", "#a73737"];

const seedNumber = (value: string) =>
  value.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);

const randomBetween = (seed: number) =>
  (Math.sin(seed) * 10000 - Math.floor(Math.sin(seed) * 10000));

const buildObstacles = (count: number, seed: number) => {
  const obstacles = [] as { x: number; y: number }[];
  for (let i = 0; i < count; i += 1) {
    const x = (randomBetween(seed + i * 13) - 0.5) * 6.0;
    const y = (randomBetween(seed + i * 29) - 0.5) * 6.0;
    obstacles.push({ x, y });
  }
  return obstacles;
};

const normalizePosition = (pos: { x: number; y: number }, bounds: number) => {
  return {
    x: (pos.x / bounds) * 3.0,
    y: (pos.y / bounds) * 3.0,
  };
};

type ThreePanelProps = {
  scenario: ScenarioResult | null;
};

export default function ThreePanel({ scenario }: ThreePanelProps) {
  const environment = scenario?.environment;
  const riskScore = environment?.risk_score ?? 0.0;
  const riskColor = useMemo(() => {
    if (riskScore >= 0.7) return surfaceColors[2];
    if (riskScore >= 0.45) return surfaceColors[1];
    return surfaceColors[0];
  }, [riskScore]);

  const startPos = parsePosition(scenario?.scenario_loaded?.start);
  const goalPos = parsePosition(scenario?.scenario_loaded?.goal);
  const roverPos = parsePosition(scenario?.navigation?.final_position);

  const sceneData = useMemo(() => {
    if (!scenario || !startPos || !goalPos || !roverPos) {
      return null;
    }
    const bounds = Math.max(
      Math.abs(startPos.x),
      Math.abs(startPos.y),
      Math.abs(goalPos.x),
      Math.abs(goalPos.y),
      Math.abs(roverPos.x),
      Math.abs(roverPos.y)
    );
    const seed = seedNumber(scenario.scenario_id);
    return {
      start: normalizePosition(startPos, bounds),
      goal: normalizePosition(goalPos, bounds),
      rover: normalizePosition(roverPos, bounds),
      obstacles: buildObstacles(environment?.obstacle_count ?? 0, seed),
      windSpeed: environment?.wind_speed ?? 0,
    };
  }, [scenario, startPos, goalPos, roverPos, environment?.obstacle_count, environment?.wind_speed]);

  if (!sceneData) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-slate-400">
        Select a scenario to render the terrain view.
      </div>
    );
  }

  return (
    <Canvas camera={{ position: [0, 5, 7], fov: 45 }}>
      <ambientLight intensity={0.5} />
      <directionalLight position={[4, 6, 2]} intensity={0.8} />

      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[8, 8, 32, 32]} />
        <meshStandardMaterial color={riskColor} metalness={0.1} roughness={0.9} />
      </mesh>

      <mesh position={[sceneData.start.x, 0.15, sceneData.start.y]}>
        <sphereGeometry args={[0.12, 32, 32]} />
        <meshStandardMaterial color="#58a6ff" />
      </mesh>

      <mesh position={[sceneData.goal.x, 0.15, sceneData.goal.y]}>
        <sphereGeometry args={[0.12, 32, 32]} />
        <meshStandardMaterial color="#22c55e" />
      </mesh>

      <mesh position={[sceneData.rover.x, 0.2, sceneData.rover.y]}>
        <boxGeometry args={[0.22, 0.18, 0.22]} />
        <meshStandardMaterial color="#f59e0b" />
      </mesh>

      <line>
        <bufferGeometry
          attach="geometry"
          setFromPoints={[
            { x: sceneData.start.x, y: 0.12, z: sceneData.start.y },
            { x: sceneData.rover.x, y: 0.12, z: sceneData.rover.y },
          ]}
        />
        <lineBasicMaterial color="#f87171" linewidth={2} />
      </line>

      {sceneData.obstacles.map((obstacle, index) => (
        <mesh key={`obs-${index}`} position={[obstacle.x, 0.12, obstacle.y]}>
          <cylinderGeometry args={[0.05, 0.05, 0.08, 12]} />
          <meshStandardMaterial color="#ef4444" />
        </mesh>
      ))}

      <mesh position={[2.8, 0.12, -2.5]} rotation={[0, 0, -Math.PI / 8]}>
        <coneGeometry args={[0.12, 0.35, 12]} />
        <meshStandardMaterial color="#38bdf8" />
      </mesh>
      <mesh position={[2.8, 0.12, -2.7]}>
        <cylinderGeometry args={[0.03, 0.03, 0.4, 12]} />
        <meshStandardMaterial color="#38bdf8" />
      </mesh>

      <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.4} />
    </Canvas>
  );
}
