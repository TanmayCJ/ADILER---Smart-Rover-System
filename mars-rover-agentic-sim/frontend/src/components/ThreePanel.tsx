import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Html, OrbitControls } from "@react-three/drei";
import type { Group, Line, LineDashedMaterial, LineSegments, Mesh, Points } from "three";
import { BufferAttribute, Color, MathUtils, PlaneGeometry, Vector3 } from "three";
import { useEffect, useMemo, useRef, useState, type MutableRefObject } from "react";

import { ScenarioResult, parsePosition } from "@/lib/demoData";

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

const normalizeToUnit = (pos: { x: number; y: number }, bounds: number) => {
  return {
    x: pos.x / bounds,
    y: pos.y / bounds,
  };
};

const ensureSeparation = (
  a: { x: number; y: number },
  b: { x: number; y: number },
  minDistance: number
) => {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const distance = Math.sqrt(dx * dx + dy * dy) || 1;
  if (distance >= minDistance) return { a, b };
  const push = (minDistance - distance) / 2;
  const nx = dx / distance;
  const ny = dy / distance;
  return {
    a: { x: a.x - nx * push, y: a.y - ny * push },
    b: { x: b.x + nx * push, y: b.y + ny * push },
  };
};

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));

const offsetLabel = (
  pos: { x: number; y: number },
  center: { x: number; y: number },
  magnitude: number,
  height: number,
  clampRange: number
) => {
  const dx = pos.x - center.x;
  const dy = pos.y - center.y;
  const len = Math.hypot(dx, dy) || 1;
  const offsetX = pos.x + (dx / len) * magnitude;
  const offsetZ = pos.y + (dy / len) * magnitude;
  return {
    x: clamp(offsetX, -clampRange, clampRange),
    y: height,
    z: clamp(offsetZ, -clampRange, clampRange),
  };
};

type ThreePanelProps = {
  scenario: ScenarioResult | null;
  roverProgress?: number;
  activePhase?: number;
};

const phaseLabels = [
  "Environment Analysis",
  "Planning",
  "Navigation",
  "Memory Update",
  "Complete",
];

type LabelPriority = "high" | "medium" | "low";

const labelStyles = {
  base: "rounded-md border border-slate-700/60 bg-slate-950/70 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-slate-200 shadow-[0_8px_24px_rgba(0,0,0,0.45)] backdrop-blur-sm",
  high: "text-slate-100",
  medium: "text-slate-300",
  low: "text-slate-400",
};

const LabelBillboard = ({
  text,
  priority,
  detail,
}: {
  text: string;
  priority: LabelPriority;
  detail?: string;
}) => {
  const { camera } = useThree();
  const [opacity, setOpacity] = useState(1);

  useFrame(() => {
    const distance = camera.position.length();
    let nextOpacity = 1;
    if (priority === "low") {
      nextOpacity = distance > 12 ? 0 : distance > 9 ? 0.35 : 0.8;
    } else if (priority === "medium") {
      nextOpacity = distance > 12 ? 0.2 : distance > 9 ? 0.6 : 1;
    }
    setOpacity(nextOpacity);
  });

  if (opacity <= 0.01) return null;

  return (
    <Html
      center
      distanceFactor={10}
      transform
      sprite
      style={{ opacity, pointerEvents: "none" }}
    >
      <div
        className={`${labelStyles.base} ${labelStyles[priority]}`}
      >
        {text}
        {detail && (
          <div className="mt-1 text-[9px] uppercase tracking-[0.14em] text-slate-400">
            {detail}
          </div>
        )}
      </div>
    </Html>
  );
};

const createTerrainGeometry = (
  size: number,
  segments: number,
  seed: number,
  risk: number,
  rocky: boolean
) => {
  const geometry = new PlaneGeometry(size, size, segments, segments);
  geometry.rotateX(-Math.PI / 2);
  const positions = geometry.attributes.position as BufferAttribute;
  const colors = new Float32Array(positions.count * 3);
  const low = new Color("#402618");
  const mid = new Color("#7a4a2b");
  const high = new Color("#a73737");
  const heightScale = rocky ? 0.22 : 0.14;
  for (let i = 0; i < positions.count; i += 1) {
    const x = positions.getX(i);
    const z = positions.getZ(i);
    const noise =
      Math.sin(x * 0.55 + seed * 0.02) * 0.6 +
      Math.cos(z * 0.48 - seed * 0.03) * 0.5 +
      Math.sin((x + z) * 0.22 + seed * 0.06) * 0.45;
    const height = noise * heightScale * (0.7 + risk * 0.8);
    positions.setY(i, height);
    const heightT = MathUtils.clamp((height + heightScale) / (heightScale * 2), 0, 1);
    const riskT = MathUtils.clamp(risk * 1.1, 0, 1);
    const terrainColor = low.clone().lerp(mid, heightT).lerp(high, riskT * 0.7);
    colors[i * 3] = terrainColor.r;
    colors[i * 3 + 1] = terrainColor.g;
    colors[i * 3 + 2] = terrainColor.b;
  }
  geometry.setAttribute("color", new BufferAttribute(colors, 3));
  geometry.computeVertexNormals();
  return geometry;
};

const DustField = ({
  count,
  spread,
  height,
  color,
  speed,
}: {
  count: number;
  spread: number;
  height: number;
  color: string;
  speed: number;
}) => {
  const ref = useRef<Points>(null);
  const positions = useMemo(() => {
    const data = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      data[i * 3] = (Math.random() - 0.5) * spread;
      data[i * 3 + 1] = Math.random() * height + 0.15;
      data[i * 3 + 2] = (Math.random() - 0.5) * spread;
    }
    return data;
  }, [count, spread, height]);

  useFrame((_, delta) => {
    if (!ref.current) return;
    const attribute = ref.current.geometry.attributes.position as BufferAttribute;
    for (let i = 0; i < attribute.count; i += 1) {
      const x = attribute.getX(i) + delta * speed;
      const z = attribute.getZ(i) + delta * speed * 0.6;
      attribute.setX(i, x > spread / 2 ? -spread / 2 : x);
      attribute.setZ(i, z > spread / 2 ? -spread / 2 : z);
    }
    attribute.needsUpdate = true;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          array={positions}
          count={positions.length / 3}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        color={color}
        size={0.06}
        transparent
        opacity={0.35}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
};

const WindStreaks = ({
  count,
  spread,
  length,
  speed,
  color,
}: {
  count: number;
  spread: number;
  length: number;
  speed: number;
  color: string;
}) => {
  const ref = useRef<LineSegments>(null);
  const positions = useMemo(() => {
    const data = new Float32Array(count * 6);
    for (let i = 0; i < count; i += 1) {
      const baseX = (Math.random() - 0.5) * spread;
      const baseY = Math.random() * 0.8 + 0.1;
      const baseZ = (Math.random() - 0.5) * spread;
      data[i * 6] = baseX;
      data[i * 6 + 1] = baseY;
      data[i * 6 + 2] = baseZ;
      data[i * 6 + 3] = baseX + length;
      data[i * 6 + 4] = baseY;
      data[i * 6 + 5] = baseZ;
    }
    return data;
  }, [count, spread, length]);

  useFrame((_, delta) => {
    if (!ref.current) return;
    const attribute = ref.current.geometry.attributes.position as BufferAttribute;
    for (let i = 0; i < attribute.count; i += 2) {
      const x = attribute.getX(i) + delta * speed;
      const x2 = attribute.getX(i + 1) + delta * speed;
      const wrappedX = x > spread / 2 ? -spread / 2 : x;
      const wrappedX2 = x2 > spread / 2 ? -spread / 2 + length : x2;
      attribute.setX(i, wrappedX);
      attribute.setX(i + 1, wrappedX2);
    }
    attribute.needsUpdate = true;
  });

  return (
    <lineSegments ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          array={positions}
          count={positions.length / 3}
          itemSize={3}
        />
      </bufferGeometry>
      <lineBasicMaterial color={color} transparent opacity={0.55} />
    </lineSegments>
  );
};

function HazardRing({
  active,
  color,
  radius,
  width,
  opacity,
  speed,
}: {
  active: boolean;
  color: string;
  radius: number;
  width: number;
  opacity: number;
  speed: number;
}) {
  const ref = useRef<Mesh>(null);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const pulse = 1 + Math.sin(clock.getElapsedTime() * speed) * 0.08;
    ref.current.scale.set(pulse, pulse, pulse);
    const material = ref.current.material as any;
    material.opacity = opacity + Math.sin(clock.getElapsedTime() * speed) * 0.05;
  });
  if (!active) return null;
  return (
    <mesh ref={ref} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 0]}>
      <ringGeometry args={[radius, radius + width, 48]} />
      <meshBasicMaterial color={color} transparent opacity={opacity} />
    </mesh>
  );
}

function FocusPulse({
  active,
  position,
  color,
}: {
  active: boolean;
  position: Vector3;
  color: string;
}) {
  const ref = useRef<Mesh>(null);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const pulse = 1 + Math.sin(clock.getElapsedTime() * 3.5) * 0.12;
    ref.current.scale.set(pulse, pulse, pulse);
    const material = ref.current.material as any;
    material.opacity = 0.2 + Math.sin(clock.getElapsedTime() * 3.5) * 0.08;
  });
  if (!active) return null;
  return (
    <mesh ref={ref} rotation={[-Math.PI / 2, 0, 0]} position={[position.x, 0.06, position.z]}>
      <ringGeometry args={[0.2, 0.45, 36]} />
      <meshBasicMaterial color={color} transparent opacity={0.2} />
    </mesh>
  );
}

function RoverRig({
  target,
  activePhase,
  lowEnergy,
}: {
  target: Vector3;
  activePhase: number;
  lowEnergy: boolean;
}) {
  const ref = useRef<Group>(null);
  const velocity = useRef(new Vector3(0, 0, 0));
  const movingRef = useRef(false);

  useFrame((state, delta) => {
    if (!ref.current) return;
    const current = ref.current.position;
    const next = current.clone().lerp(target, 1 - Math.pow(0.02, delta));
    const move = next.clone().sub(current);
    velocity.current.lerp(move, 0.3);
    movingRef.current = velocity.current.length() > 0.0005;
    current.copy(next);
    const tiltX = MathUtils.clamp(-velocity.current.z * 6, -0.25, 0.25);
    const tiltZ = MathUtils.clamp(velocity.current.x * 6, -0.25, 0.25);
    ref.current.rotation.x = MathUtils.lerp(ref.current.rotation.x, tiltX, 0.08);
    ref.current.rotation.z = MathUtils.lerp(ref.current.rotation.z, tiltZ, 0.08);
    if (activePhase === 2) {
      ref.current.position.y = 0.22 + Math.sin(state.clock.getElapsedTime() * 3) * 0.01;
    }
  });

  return (
    <group ref={ref} position={[target.x, 0.22, target.z]}>
      <PulsingRover active={activePhase === 2} moving={movingRef} lowEnergy={lowEnergy} />
      {activePhase === 2 && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.12, 0]}>
          <ringGeometry args={[0.12, 0.32, 24]} />
          <meshBasicMaterial color="#38bdf8" transparent opacity={0.18} />
        </mesh>
      )}
    </group>
  );
}

function ControlsRig({
  controls,
  focus,
  activePhase,
}: {
  controls: MutableRefObject<any>;
  focus: Vector3;
  activePhase: number;
}) {
  const { camera } = useThree();
  const focusRef = useRef(focus);
  useEffect(() => {
    focusRef.current = focus;
  }, [focus]);
  useFrame((state, delta) => {
    if (!controls.current) return;
    if (controls.current.__isUserInteracting) return;
    const target = controls.current.target;
    const desiredTarget = new Vector3(focusRef.current.x, 0.2, focusRef.current.z);
    target.lerp(desiredTarget, 1 - Math.pow(0.08, delta));
    if (activePhase === 2) {
      const desiredPos = desiredTarget.clone().add(new Vector3(2.2, 4.0, 4.6));
      camera.position.lerp(desiredPos, 1 - Math.pow(0.05, delta));
    }
    controls.current.update();
  });
  return null;
}

function SceneAnimator({
  activePhase,
  plannedMaterialRef,
  windRef,
  windDirection,
}: {
  activePhase: number;
  plannedMaterialRef: MutableRefObject<LineDashedMaterial | null>;
  windRef: MutableRefObject<Group | null>;
  windDirection: number;
}) {
  useFrame((state, delta) => {
    if (plannedMaterialRef.current) {
      const material = plannedMaterialRef.current;
      const targetOpacity = activePhase >= 1 ? 0.85 : 0;
      material.opacity = MathUtils.lerp(material.opacity ?? 1, targetOpacity, 0.08);
      material.dashOffset -= delta * 0.6;
      material.needsUpdate = true;
    }
    if (windRef.current) {
      const sway = Math.sin(state.clock.getElapsedTime() * 1.4) * 0.08;
      windRef.current.rotation.z = windDirection + sway;
    }
  });
  return null;
}

function PulsingRover({
  active,
  moving,
  lowEnergy,
}: {
  active: boolean;
  moving: { current: boolean };
  lowEnergy: boolean;
}) {
  const ref = useRef<Mesh>(null);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const motionPulse = moving.current ? 1 + Math.sin(clock.getElapsedTime() * 5) * 0.06 : 1;
    const pulse = active ? 1 + Math.sin(clock.getElapsedTime() * 6) * 0.08 : 1;
    ref.current.scale.set(pulse, pulse, pulse);
    const glow = lowEnergy ? 0.08 : moving.current ? 0.45 : active ? 0.35 : 0.2;
    (ref.current.material as any).emissiveIntensity = glow;
    ref.current.scale.multiplyScalar(motionPulse);
  });
  return (
    <mesh ref={ref}>
      <boxGeometry args={[0.22, 0.18, 0.22]} />
      <meshStandardMaterial
        color={lowEnergy ? "#64748b" : "#3b82f6"}
        emissive={lowEnergy ? "#0f172a" : "#1d4ed8"}
        emissiveIntensity={lowEnergy ? 0.08 : active ? 0.4 : 0.2}
        metalness={0.3}
        roughness={0.6}
      />
    </mesh>
  );
}

export default function ThreePanel({
  scenario,
  roverProgress = 1,
  activePhase = -1,
}: ThreePanelProps) {
  const environment = scenario?.environment;
  const riskScore = environment?.risk_score ?? 0.0;
  const scenarioId = scenario?.scenario_id?.toLowerCase() ?? "";
  const isEasy = scenarioId.includes("easy");
  const isHighWind = scenarioId.includes("high_wind");
  const isDustStorm = scenarioId.includes("dust");
  const isRocky = scenarioId.includes("rocky");
  const isEnergyCritical = scenarioId.includes("energy_critical");

  const startPos = parsePosition(scenario?.scenario_loaded?.start);
  const goalPos = parsePosition(scenario?.scenario_loaded?.goal);
  const action = scenario?.planner?.action ?? "proceed";
  const roverInitial = parsePosition(scenario?.navigation?.initial_position);
  const roverFinal = parsePosition(scenario?.navigation?.final_position);
  const plannedLineRef = useRef<Line>(null);
  const plannedMaterialRef = useRef<LineDashedMaterial>(null);
  const windRef = useRef<Group>(null);
  const controlsRef = useRef<any>(null);

  const sceneData = useMemo(() => {
    if (!scenario || !startPos || !goalPos || !roverInitial || !roverFinal) {
      return null;
    }
    const bounds = Math.max(
      Math.abs(startPos.x),
      Math.abs(startPos.y),
      Math.abs(goalPos.x),
      Math.abs(goalPos.y),
      Math.abs(roverFinal.x),
      Math.abs(roverFinal.y)
    );
    const seed = seedNumber(scenario.scenario_id);
    const interpolated = {
      x: roverInitial.x + (roverFinal.x - roverInitial.x) * roverProgress,
      y: roverInitial.y + (roverFinal.y - roverInitial.y) * roverProgress,
    };
    const unitStart = normalizeToUnit(startPos, bounds);
    const unitGoal = normalizeToUnit(goalPos, bounds);
    const unitRoverInitial = normalizeToUnit(roverInitial, bounds);
    const unitRover = normalizeToUnit(interpolated, bounds);
    const unitGoalDelta = {
      x: unitGoal.x - unitStart.x,
      y: unitGoal.y - unitStart.y,
    };
    const unitDistance = Math.hypot(unitGoalDelta.x, unitGoalDelta.y) || 1;
    const scenarioScale = isEnergyCritical
      ? 1.45
      : isHighWind
        ? 1.25
        : isDustStorm
          ? 1.15
          : isRocky
            ? 1.1
            : 1.0;
    const baseScale = 6.8 * scenarioScale;
    const minSpan = isEnergyCritical
      ? 7.2
      : isHighWind
        ? 6.2
        : isDustStorm
          ? 5.8
          : isRocky
            ? 5.6
            : 5.2;
    const initialSpan = unitDistance * baseScale;
    const spanScale = initialSpan < minSpan ? minSpan / initialSpan : 1;
    const finalScale = baseScale * spanScale;
    const start = { x: unitStart.x * finalScale, y: unitStart.y * finalScale };
    const goal = { x: unitGoal.x * finalScale, y: unitGoal.y * finalScale };
    const missionVector = { x: goal.x - start.x, y: goal.y - start.y };
    const missionSpan = Math.hypot(missionVector.x, missionVector.y) || 1;
    const missionDir = {
      x: missionVector.x / missionSpan,
      y: missionVector.y / missionSpan,
    };
    const missionPerp = { x: -missionDir.y, y: missionDir.x };
    const missionMid = {
      x: (start.x + goal.x) / 2,
      y: (start.y + goal.y) / 2,
    };
    const roverStartDistance = Math.hypot(
      unitRoverInitial.x - unitStart.x,
      unitRoverInitial.y - unitStart.y
    );
    const roverStartT = Math.min(0.12, roverStartDistance / (unitDistance || 1));
    const roverT = MathUtils.clamp(
      (unitRover.x - unitStart.x) * (unitGoalDelta.x / (unitDistance || 1)) +
        (unitRover.y - unitStart.y) * (unitGoalDelta.y / (unitDistance || 1)),
      0.12,
      isEnergyCritical ? 0.45 : 0.88
    );
    const lateralOffset =
      (action === "reroute" ? 0.18 : isHighWind ? 0.12 : 0.08) *
      (seed % 2 === 0 ? 1 : -1);
    const roverStart = {
      x: start.x + missionDir.x * missionSpan * roverStartT,
      y: start.y + missionDir.y * missionSpan * roverStartT,
    };
    const rover = {
      x:
        start.x +
        missionDir.x * missionSpan * roverT +
        missionPerp.x * missionSpan * lateralOffset * 0.15,
      y:
        start.y +
        missionDir.y * missionSpan * roverT +
        missionPerp.y * missionSpan * lateralOffset * 0.15,
    };
    const curveStrength =
      action === "reroute"
        ? missionSpan * 0.28
        : isRocky
          ? missionSpan * 0.22
          : isHighWind
            ? missionSpan * 0.18
            : missionSpan * 0.12;
    const plannedMid = {
      x: missionMid.x + missionPerp.x * curveStrength,
      y: missionMid.y + missionPerp.y * curveStrength,
    };
    const obstacleCount = environment?.obstacle_count ?? 0;
    const maxMarkers = isRocky ? 10 : 7;
    const markerCount = obstacleCount > maxMarkers ? maxMarkers : obstacleCount;
    const obstacleSpread = missionSpan * (isRocky ? 0.45 : 0.32);
    const obstacleAnchor = {
      x: missionMid.x + missionPerp.x * missionSpan * (isRocky ? 0.25 : 0.15),
      y: missionMid.y + missionPerp.y * missionSpan * (isRocky ? 0.25 : 0.15),
    };
    const obstacles = buildObstacles(markerCount, seed).map((obs, index) => {
      const scaleX = (obs.x / 3) * obstacleSpread * 0.45;
      const scaleY = (obs.y / 3) * obstacleSpread * 0.45;
      return {
        x: obstacleAnchor.x + scaleX,
        y: obstacleAnchor.y + scaleY,
        seed: seed + index * 31,
      };
    });
    const windDirection = (seed % 360) * (Math.PI / 180);
    const spaced = ensureSeparation(start, goal, Math.max(2.4, missionSpan * 0.3));
    const spacedRover = ensureSeparation(rover, spaced.b, Math.max(1.2, missionSpan * 0.18));
    return {
      start: spaced.a,
      goal: spaced.b,
      rover: spacedRover.a,
      roverStart,
      plannedMid,
      obstacles,
      windSpeed: environment?.wind_speed ?? 0,
      windDirection,
      obstacleCount,
      obstacleCenter: obstacles.reduce(
        (acc, obs) => ({ x: acc.x + obs.x, y: acc.y + obs.y }),
        { x: 0, y: 0 }
      ),
      missionMid,
      missionSpan,
      missionDir,
      missionPerp,
    };
  }, [
    scenario,
    startPos,
    goalPos,
    roverInitial,
    roverFinal,
    environment?.risk_score,
    environment?.obstacle_count,
    environment?.wind_speed,
    roverProgress,
    action,
    isRocky,
    isDustStorm,
    isHighWind,
    isEnergyCritical,
  ]);

  useEffect(() => {
    if (!sceneData || !plannedLineRef.current) return;
    const geometry = plannedLineRef.current.geometry;
    const positions = geometry?.attributes?.position;
    if (!positions || positions.count < 2) return;
    plannedLineRef.current.computeLineDistances();
  }, [sceneData, activePhase]);


  const terrainSeed = seedNumber(scenario?.scenario_id ?? "terrain");
  const terrainSize = MathUtils.clamp((sceneData?.missionSpan ?? 6) * 2.6, 12, 20);
  const terrainGeometry = useMemo(
    () => createTerrainGeometry(terrainSize, 30, terrainSeed, riskScore, isRocky),
    [terrainSize, terrainSeed, riskScore, isRocky]
  );
  const roverFocus = useMemo(
    () => new Vector3(sceneData?.rover.x ?? 0, 0, sceneData?.rover.y ?? 0),
    [sceneData?.rover.x, sceneData?.rover.y]
  );
  const roverTarget = useMemo(
    () => new Vector3(sceneData?.rover.x ?? 0, 0, sceneData?.rover.y ?? 0),
    [sceneData?.rover.x, sceneData?.rover.y]
  );

  if (!sceneData) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-slate-400">
        Select a scenario to render the terrain view.
      </div>
    );
  }

  const windScale = Math.min((sceneData.windSpeed ?? 0) / 10, 1.6) + 0.35;
  const windBoost = isHighWind ? 1.6 : action === "reduce_speed" ? 1.4 : 1.0;
  const windColor = isHighWind ? "#38bdf8" : action === "reduce_speed" ? "#0ea5e9" : "#38bdf8";
  const obstacleEmphasis = action === "hold_position" ? 0.18 : 0.1;
  const phaseHighlight = phaseLabels[activePhase] ?? "Standby";
  const fogColor = isDustStorm ? "#5c341d" : isEnergyCritical ? "#0b0d12" : "#1f1410";
  const fogNear = isEasy ? terrainSize * 0.55 : isDustStorm ? terrainSize * 0.4 : terrainSize * 0.48;
  const fogFar = isDustStorm ? terrainSize * 0.95 : isEnergyCritical ? terrainSize * 0.9 : terrainSize * 1.2;
  const ambientIntensity = isEnergyCritical ? 0.28 : 0.45;
  const sunIntensity = isDustStorm ? 0.55 : 0.9;
  const terrainEmissive = riskScore > 0.55 ? "#b45309" : "#000000";
  const terrainEmissiveIntensity = riskScore > 0.55 ? (isEnergyCritical ? 0.06 : 0.18 + riskScore * 0.15) : 0.02;
  const hazardOpacity = activePhase === 0 ? (isDustStorm ? 0.3 : 0.16) : isDustStorm ? 0.18 : 0.08;
  const dustRingOpacity = activePhase === 0 ? 0.26 : 0.18;
  const obstacleCenter = sceneData.obstacles.length
    ? {
        x: sceneData.obstacleCenter.x / sceneData.obstacles.length,
        y: sceneData.obstacleCenter.y / sceneData.obstacles.length,
      }
    : { x: 0, y: 0 };
  const baseCenter = {
    x: sceneData.missionMid.x,
    y: sceneData.missionMid.y,
  };
  const startRoverDistance = Math.hypot(
    sceneData.start.x - sceneData.rover.x,
    sceneData.start.y - sceneData.rover.y
  );
  const combineStartRover = startRoverDistance < Math.max(0.7, sceneData.missionSpan * 0.12);
  const combinedPoint = {
    x: (sceneData.start.x + sceneData.rover.x) / 2,
    y: (sceneData.start.y + sceneData.rover.y) / 2,
  };
  const clampRange = terrainSize / 2 - 0.8;
  const startLabel = offsetLabel(sceneData.start, baseCenter, 0.55, 0.5, clampRange);
  const goalLabel = offsetLabel(sceneData.goal, baseCenter, 0.6, 0.55, clampRange);
  const roverLabel = offsetLabel(sceneData.rover, baseCenter, 0.5, 0.55, clampRange);
  const combinedLabel = offsetLabel(combinedPoint, baseCenter, 0.6, 0.52, clampRange);
  const obstacleLabel = offsetLabel(obstacleCenter, baseCenter, 0.65, 0.65, clampRange);
  const dustCount = isDustStorm ? 140 : isEasy ? 70 : 100;
  const dustSpeed = isDustStorm ? 0.25 : 0.12;
  const windStreakCount = isHighWind ? 36 : 18;
  const windStreakSpeed = isHighWind ? 0.9 : 0.55;
  const dustSpread = terrainSize * 0.95;
  const windAnchor = {
    x: sceneData.missionMid.x + sceneData.missionPerp.x * sceneData.missionSpan * (isHighWind ? 0.25 : 0.18),
    y: sceneData.missionMid.y + sceneData.missionPerp.y * sceneData.missionSpan * (isHighWind ? 0.25 : 0.18),
  };

  return (
    <Canvas key={scenarioId} camera={{ position: [0, 5.8, 7.4], fov: 40 }}>
      <color attach="background" args={[new Color(fogColor)]} />
      <fog attach="fog" args={[new Color(fogColor), fogNear, fogFar]} />
      <ambientLight intensity={ambientIntensity} color="#7c3f21" />
      <directionalLight position={[4, 6, 2]} intensity={sunIntensity} color="#f8d4b4" />
      <hemisphereLight args={["#a84f2a", "#1f1210", 0.25]} />

      <gridHelper args={[10, 20, "#1f2937", "#111827"]} position={[0, 0.01, 0]} />

      <mesh key={`${scenarioId}-terrain`} rotation={[-Math.PI / 2, 0, 0]}>
        <primitive attach="geometry" object={terrainGeometry} />
        <meshStandardMaterial
          vertexColors
          flatShading
          metalness={0.1}
          roughness={0.95}
          emissive={terrainEmissive}
          emissiveIntensity={terrainEmissiveIntensity}
        />
      </mesh>

      <HazardRing
        key={`${scenarioId}-hazard`}
        active={riskScore > 0.55}
        color="#f97316"
        radius={2.2}
        width={0.5}
        opacity={hazardOpacity}
        speed={isDustStorm ? 2.4 : 1.6}
      />
      <HazardRing
        key={`${scenarioId}-dust-ring`}
        active={isDustStorm}
        color="#fb923c"
        radius={3.4}
        width={0.7}
        opacity={dustRingOpacity}
        speed={2.8}
      />

      <DustField
        key={`${scenarioId}-dust-${dustCount}`}
        count={dustCount}
        spread={9}
        height={2.4}
        color={isDustStorm ? "#f59e0b" : "#e2b089"}
        speed={dustSpeed}
      />

      {action === "hold_position" && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 0]}>
          <ringGeometry args={[1.8, 3.2, 32]} />
          <meshBasicMaterial color="#ef4444" transparent opacity={obstacleEmphasis} />
        </mesh>
      )}

      <mesh position={[sceneData.start.x, 0.15, sceneData.start.y]}>
        <sphereGeometry args={[0.12, 32, 32]} />
        <meshStandardMaterial color="#22c55e" />
      </mesh>
      {combineStartRover ? (
        <>
          <group position={[combinedLabel.x, combinedLabel.y, combinedLabel.z]}>
            <LabelBillboard text="Start / Rover" priority="medium" />
          </group>
          <line>
            <bufferGeometry
              attach="geometry"
              setFromPoints={[
                new Vector3(combinedPoint.x, 0.12, combinedPoint.y),
                new Vector3(combinedLabel.x, combinedLabel.y, combinedLabel.z),
              ]}
            />
            <lineBasicMaterial color="#22c55e" />
          </line>
        </>
      ) : (
        <>
          <group position={[startLabel.x, startLabel.y, startLabel.z]}>
            <LabelBillboard text="Start" priority="medium" />
          </group>
          <line>
            <bufferGeometry
              attach="geometry"
              setFromPoints={[
                new Vector3(sceneData.start.x, 0.12, sceneData.start.y),
                new Vector3(startLabel.x, startLabel.y, startLabel.z),
              ]}
            />
            <lineBasicMaterial color="#22c55e" />
          </line>
        </>
      )}

      <mesh position={[sceneData.goal.x, 0.15, sceneData.goal.y]}>
        <sphereGeometry args={[0.12, 32, 32]} />
        <meshStandardMaterial color="#facc15" />
      </mesh>
      <group position={[goalLabel.x, goalLabel.y, goalLabel.z]}>
        <LabelBillboard text="Goal" priority="high" />
      </group>
      <line>
        <bufferGeometry
          attach="geometry"
          setFromPoints={[
            new Vector3(sceneData.goal.x, 0.12, sceneData.goal.y),
            new Vector3(goalLabel.x, goalLabel.y, goalLabel.z),
          ]}
        />
        <lineBasicMaterial color="#facc15" />
      </line>

      <RoverRig target={roverTarget} activePhase={activePhase} lowEnergy={isEnergyCritical} />
      {!combineStartRover && (
        <>
          <group position={[roverLabel.x, roverLabel.y, roverLabel.z]}>
            <LabelBillboard text="Rover" priority="high" />
          </group>
          <line>
            <bufferGeometry
              attach="geometry"
              setFromPoints={[
                new Vector3(sceneData.rover.x, 0.12, sceneData.rover.y),
                new Vector3(roverLabel.x, roverLabel.y, roverLabel.z),
              ]}
            />
            <lineBasicMaterial color="#3b82f6" />
          </line>
        </>
      )}

      <FocusPulse
        active={activePhase === 3}
        position={roverTarget}
        color={isEnergyCritical ? "#94a3b8" : "#38bdf8"}
      />

      <line key={`${scenarioId}-planned`} ref={plannedLineRef}>
        <bufferGeometry
          attach="geometry"
          setFromPoints={[
            new Vector3(sceneData.start.x, 0.12, sceneData.start.y),
            new Vector3(sceneData.plannedMid.x, 0.12, sceneData.plannedMid.y),
            new Vector3(sceneData.goal.x, 0.12, sceneData.goal.y),
          ]}
        />
        <lineDashedMaterial
          ref={plannedMaterialRef}
          color={activePhase === 1 ? "#e2e8f0" : "#94a3b8"}
          dashSize={0.2}
          gapSize={0.12}
          transparent
          opacity={activePhase >= 1 ? 0.85 : 0}
        />
      </line>

      <line key={`${scenarioId}-executed`}>
        <bufferGeometry
          attach="geometry"
          setFromPoints={[
            new Vector3(sceneData.roverStart.x, 0.12, sceneData.roverStart.y),
            new Vector3(sceneData.rover.x, 0.12, sceneData.rover.y),
          ]}
        />
        <lineBasicMaterial
          color="#fb7185"
          linewidth={2}
          transparent
          opacity={activePhase >= 2 ? 0.95 : 0.2}
        />
      </line>

      {sceneData.obstacles.map((obstacle, index) => (
        <mesh key={`obs-${index}`} position={[obstacle.x, 0.1, obstacle.y]}>
          <cylinderGeometry args={[0.06, 0.06, 0.12, 12]} />
          <meshStandardMaterial
            color="#ef4444"
            emissive="#ef4444"
            emissiveIntensity={isRocky || riskScore > 0.6 ? 0.35 : activePhase === 0 ? 0.4 : 0.15}
          />
        </mesh>
      ))}

      {sceneData.obstacles.length > 0 && (
        <>
          <group position={[obstacleLabel.x, obstacleLabel.y, obstacleLabel.z]}>
            <LabelBillboard
              text="Obstacle Field"
              priority="low"
              detail={`Count: ${sceneData.obstacleCount ?? sceneData.obstacles.length}`}
            />
          </group>
          <line>
            <bufferGeometry
              attach="geometry"
              setFromPoints={[
                new Vector3(obstacleCenter.x, 0.12, obstacleCenter.y),
                new Vector3(obstacleLabel.x, obstacleLabel.y, obstacleLabel.z),
              ]}
            />
            <lineBasicMaterial color="#ef4444" />
          </line>
        </>
      )}

      <group
        ref={windRef}
        position={[3.0, 0.12, -3.2]}
        rotation={[0, 0, sceneData.windDirection]}
        scale={[windScale * windBoost, windScale * windBoost, windScale * windBoost]}
      >
        <WindStreaks
          key={`${scenarioId}-wind-${windStreakCount}`}
          count={windStreakCount}
          spread={2.4}
          length={0.35}
          speed={windStreakSpeed}
          color={windColor}
        />
        <mesh rotation={[0, 0, -Math.PI / 8]}>
          <coneGeometry args={[0.12, 0.35, 12]} />
          <meshStandardMaterial color={windColor} />
        </mesh>
        <mesh position={[0, -0.18, 0]}>
          <cylinderGeometry args={[0.03, 0.03, 0.4, 12]} />
          <meshStandardMaterial color={windColor} />
        </mesh>
        <line>
          <bufferGeometry
            attach="geometry"
            setFromPoints={[
              new Vector3(0, 0.1, 0),
              new Vector3(0.55, 0.9, 0.05),
            ]}
          />
          <lineBasicMaterial color={windColor} />
        </line>
        <group position={[0.62, 0.95, 0.08]}>
          <LabelBillboard text="Wind" priority="low" />
        </group>
      </group>

      <SceneAnimator
        activePhase={activePhase}
        plannedMaterialRef={plannedMaterialRef}
        windRef={windRef}
        windDirection={sceneData.windDirection}
      />
      <ControlsRig controls={controlsRef} focus={roverFocus} activePhase={activePhase} />

      <Html fullscreen>
        <div className="pointer-events-none absolute left-4 top-4 rounded-xl border border-slate-700/70 bg-slate-950/70 px-3 py-2 text-[11px] uppercase tracking-[0.2em] text-slate-300">
          {phaseHighlight}
        </div>
        <div className="pointer-events-none absolute bottom-4 right-4 w-36 rounded-xl border border-slate-700/70 bg-slate-950/80 px-3 py-2 text-[9px] text-slate-300">
          <p className="mb-2 text-[9px] uppercase tracking-[0.18em] text-slate-500">Legend</p>
          <ul className="space-y-1">
            <li><span className="text-emerald-300">Green</span> = Start</li>
            <li><span className="text-blue-300">Blue</span> = Rover</li>
            <li><span className="text-yellow-300">Yellow</span> = Goal</li>
            <li><span className="text-red-300">Red</span> = Obstacle</li>
            <li><span className="text-sky-300">Cyan Arrow</span> = Wind</li>
            <li><span className="text-slate-300">Dotted</span> = Planned Path</li>
            <li><span className="text-rose-300">Solid</span> = Executed Path</li>
          </ul>
        </div>
      </Html>

      <OrbitControls
        ref={controlsRef}
        makeDefault
        target={[baseCenter.x, 0.2, baseCenter.y]}
        enableZoom
        minDistance={4.6}
        maxDistance={10.5}
        enablePan={false}
        enableDamping
        dampingFactor={0.08}
        autoRotate={activePhase < 4}
        autoRotateSpeed={activePhase === 2 ? 0.18 : 0.3}
        onStart={() => {
          if (controlsRef.current) controlsRef.current.__isUserInteracting = true;
        }}
        onEnd={() => {
          if (controlsRef.current) controlsRef.current.__isUserInteracting = false;
        }}
      />
    </Canvas>
  );
}
