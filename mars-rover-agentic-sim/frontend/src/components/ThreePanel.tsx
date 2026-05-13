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
  base: "max-w-[80px] rounded border border-slate-700/60 bg-slate-950/75 px-1.5 py-0.5 text-[9px] uppercase tracking-[0.08em] text-slate-200 shadow-[0_6px_18px_rgba(0,0,0,0.45)] backdrop-blur-sm",
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
      distanceFactor={8}
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
  rocky: boolean,
  dustLevel: number,
  dustStorm: boolean,
  energyCritical: boolean,
  easy: boolean
) => {
  const geometry = new PlaneGeometry(size, size, segments, segments);
  geometry.rotateX(-Math.PI / 2);
  const positions = geometry.attributes.position as BufferAttribute;
  const colors = new Float32Array(positions.count * 3);
  const low = new Color(energyCritical ? "#231312" : "#402618");
  const mid = new Color(dustStorm ? "#8b4b28" : "#7a4a2b");
  const high = new Color(dustStorm ? "#c4632c" : "#a73737");
  const dustTint = new Color("#c27b3b");
  const heightScale = rocky ? 0.26 : dustStorm ? 0.2 : easy ? 0.12 : 0.16;
  const variationScale = rocky ? 0.14 : dustStorm ? 0.1 : 0.08;
  for (let i = 0; i < positions.count; i += 1) {
    const x = positions.getX(i);
    const z = positions.getZ(i);
    const noise =
      Math.sin(x * 0.55 + seed * 0.02) * 0.6 +
      Math.cos(z * 0.48 - seed * 0.03) * 0.5 +
      Math.sin((x + z) * 0.22 + seed * 0.06) * 0.45 +
      Math.sin((x - z) * 0.18 + seed * 0.08) * variationScale;
    const height = noise * heightScale * (0.7 + risk * 0.8);
    positions.setY(i, height);
    const heightT = MathUtils.clamp((height + heightScale) / (heightScale * 2), 0, 1);
    const riskT = MathUtils.clamp(risk * 1.1, 0, 1);
    const terrainColor = low.clone().lerp(mid, heightT).lerp(high, riskT * 0.7);
    const dustBlend = MathUtils.clamp(dustLevel, 0, 1) * (dustStorm ? 0.65 : 0.35);
    terrainColor.lerp(dustTint, dustBlend);
    if (energyCritical) {
      terrainColor.multiplyScalar(0.85);
    }
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
  roverRef,
  movementDamping,
  tiltScale,
  visibility,
}: {
  target: Vector3;
  activePhase: number;
  lowEnergy: boolean;
  roverRef: MutableRefObject<Group | null>;
  movementDamping: number;
  tiltScale: number;
  visibility: number;
}) {
  const velocity = useRef(new Vector3(0, 0, 0));
  const movingRef = useRef(false);
  const yawRef = useRef(0);

  useFrame((state, delta) => {
    if (!roverRef.current) return;
    const current = roverRef.current.position;
    const next = current.clone().lerp(target, 1 - Math.pow(movementDamping, delta));
    const move = next.clone().sub(current);
    velocity.current.lerp(move, 0.3);
    movingRef.current = velocity.current.length() > 0.0005;
    current.copy(next);
    const tiltX = MathUtils.clamp(-velocity.current.z * tiltScale, -0.25, 0.25);
    const tiltZ = MathUtils.clamp(velocity.current.x * tiltScale, -0.25, 0.25);
    roverRef.current.rotation.x = MathUtils.lerp(roverRef.current.rotation.x, tiltX, 0.08);
    roverRef.current.rotation.z = MathUtils.lerp(roverRef.current.rotation.z, tiltZ, 0.08);
    if (movingRef.current) {
      const desiredYaw = Math.atan2(velocity.current.x, velocity.current.z);
      const deltaYaw = MathUtils.euclideanModulo(desiredYaw - yawRef.current + Math.PI, Math.PI * 2) - Math.PI;
      yawRef.current += deltaYaw * 0.12;
    }
    roverRef.current.rotation.y = MathUtils.lerp(roverRef.current.rotation.y, yawRef.current, 0.12);
    if (activePhase === 2) {
      roverRef.current.position.y = 0.22 + Math.sin(state.clock.getElapsedTime() * 3) * 0.01;
    } else {
      roverRef.current.position.y = MathUtils.lerp(roverRef.current.position.y, 0.22, 0.2);
    }
  });

  return (
    <group ref={roverRef} position={[target.x, 0.22, target.z]}>
      <PulsingRover
        active={activePhase === 2}
        moving={movingRef}
        lowEnergy={lowEnergy}
        visibility={visibility}
      />
      {activePhase === 2 && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.12, 0]}>
          <ringGeometry args={[0.12, 0.32, 24]} />
          <meshBasicMaterial color="#38bdf8" transparent opacity={0.18} />
        </mesh>
      )}
    </group>
  );
}

function RoverTrail({
  roverRef,
  activePhase,
  color,
  maxPoints = 60,
}: {
  roverRef: MutableRefObject<Group | null>;
  activePhase: number;
  color: string;
  maxPoints?: number;
}) {
  const lineRef = useRef<Line>(null);
  const positions = useMemo(() => new Float32Array(maxPoints * 3), [maxPoints]);
  const colors = useMemo(() => new Float32Array(maxPoints * 3), [maxPoints]);
  const agesRef = useRef<number[]>([]);
  const countRef = useRef(0);
  const lastPosRef = useRef<Vector3 | null>(null);
  const trailColor = useMemo(() => new Color(color), [color]);
  const fadeDuration = 4;

  useFrame((_, delta) => {
    if (!lineRef.current) return;
    if (roverRef.current) {
      const current = roverRef.current.position.clone();
      current.y = 0.08;
      const last = lastPosRef.current;
      const moved = !last || current.distanceTo(last) > 0.03;
      if (activePhase === 2 && moved) {
        if (countRef.current < maxPoints) {
          const index = countRef.current;
          positions[index * 3] = current.x;
          positions[index * 3 + 1] = current.y;
          positions[index * 3 + 2] = current.z;
          agesRef.current[index] = 0;
          countRef.current += 1;
        } else {
          for (let i = 1; i < maxPoints; i += 1) {
            positions[(i - 1) * 3] = positions[i * 3];
            positions[(i - 1) * 3 + 1] = positions[i * 3 + 1];
            positions[(i - 1) * 3 + 2] = positions[i * 3 + 2];
            agesRef.current[i - 1] = agesRef.current[i];
          }
          const index = maxPoints - 1;
          positions[index * 3] = current.x;
          positions[index * 3 + 1] = current.y;
          positions[index * 3 + 2] = current.z;
          agesRef.current[index] = 0;
        }
        lastPosRef.current = current;
      }
    }

    for (let i = 0; i < countRef.current; i += 1) {
      agesRef.current[i] = (agesRef.current[i] ?? 0) + delta;
      const intensity = MathUtils.clamp(1 - agesRef.current[i] / fadeDuration, 0, 1);
      colors[i * 3] = trailColor.r * intensity;
      colors[i * 3 + 1] = trailColor.g * intensity;
      colors[i * 3 + 2] = trailColor.b * intensity;
    }

    const geometry = lineRef.current.geometry as any;
    geometry.setDrawRange(0, countRef.current);
    geometry.attributes.position.needsUpdate = true;
    geometry.attributes.color.needsUpdate = true;
  });

  return (
    <line ref={lineRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          array={positions}
          count={positions.length / 3}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          array={colors}
          count={colors.length / 3}
          itemSize={3}
        />
      </bufferGeometry>
      <lineBasicMaterial
        vertexColors
        transparent
        opacity={0.7}
        color={trailColor}
      />
    </line>
  );
}

function ControlsRig({
  controls,
  focus,
  activePhase,
  shakeIntensity,
  shakeSpeed,
}: {
  controls: MutableRefObject<any>;
  focus: Vector3;
  activePhase: number;
  shakeIntensity: number;
  shakeSpeed: number;
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
      const basePos = desiredTarget.clone().add(new Vector3(2.2, 4.0, 4.6));
      const t = state.clock.getElapsedTime();
      const shake =
        shakeIntensity > 0
          ? new Vector3(
              Math.sin(t * shakeSpeed) * shakeIntensity,
              Math.cos(t * shakeSpeed * 0.7) * shakeIntensity * 0.4,
              Math.sin(t * shakeSpeed * 1.2) * shakeIntensity * 0.6
            )
          : new Vector3(0, 0, 0);
      const desiredPos = basePos.add(shake);
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
  visibility,
}: {
  active: boolean;
  moving: { current: boolean };
  lowEnergy: boolean;
  visibility: number;
}) {
  const ref = useRef<Mesh>(null);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const motionPulse = moving.current ? 1 + Math.sin(clock.getElapsedTime() * 5) * 0.06 : 1;
    const pulse = active ? 1 + Math.sin(clock.getElapsedTime() * 6) * 0.08 : 1;
    ref.current.scale.set(pulse, pulse, pulse);
    const glow = lowEnergy ? 0.08 : moving.current ? 0.45 : active ? 0.35 : 0.2;
    const material = ref.current.material as any;
    material.emissiveIntensity = glow;
    material.opacity = visibility;
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
        transparent
        opacity={visibility}
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
  const roverRef = useRef<Group>(null);
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
  const dustLevel = environment?.dust_level ?? 0;
  const terrainGeometry = useMemo(
    () =>
      createTerrainGeometry(
        terrainSize,
        30,
        terrainSeed,
        riskScore,
        isRocky,
        dustLevel,
        isDustStorm,
        isEnergyCritical,
        isEasy
      ),
    [
      terrainSize,
      terrainSeed,
      riskScore,
      isRocky,
      dustLevel,
      isDustStorm,
      isEnergyCritical,
      isEasy,
    ]
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

  const windScale = Math.min((sceneData.windSpeed ?? 0) / 10, 1.8) + 0.35;
  const windBoost = isHighWind ? 1.8 : action === "reduce_speed" ? 1.4 : 1.0;
  const windColor = isHighWind ? "#38bdf8" : action === "reduce_speed" ? "#0ea5e9" : "#38bdf8";
  const obstacleEmphasis = action === "hold_position" ? 0.22 : isRocky ? 0.16 : 0.1;
  const phaseHighlight = phaseLabels[activePhase] ?? "Standby";
  const scenarioName = scenario?.scenario_id ?? "Unknown Scenario";
  const telemetryRisk = environment?.risk_score ?? 0;
  const telemetryWind = environment?.wind_speed ?? 0;
  const telemetryDust = dustLevel;
  const telemetryObstacles = environment?.obstacle_count ?? 0;
  const progressPercent = Math.round(MathUtils.clamp(roverProgress, 0, 1) * 100);
  const telemetryPhase = activePhase >= 4 ? "MISSION COMPLETE" : phaseHighlight;
  const fogColor = isDustStorm ? "#6a3a1f" : isEnergyCritical ? "#0b0d12" : isEasy ? "#2a1b14" : "#1f1410";
  const fogNear = isEasy
    ? terrainSize * 0.62
    : isDustStorm
      ? terrainSize * 0.32
      : terrainSize * 0.46;
  const fogFar = isDustStorm
    ? terrainSize * 0.78
    : isEnergyCritical
      ? terrainSize * 0.92
      : terrainSize * 1.18;
  const ambientIntensity = isEnergyCritical ? 0.2 : isEasy ? 0.52 : 0.4;
  const sunIntensity = isDustStorm ? 0.48 : isEasy ? 1.05 : isEnergyCritical ? 0.65 : 0.9;
  const fillIntensity = isHighWind ? 0.35 : isDustStorm ? 0.28 : 0.22;
  const fillColor = isDustStorm ? "#b45309" : isEnergyCritical ? "#1f2937" : "#a8552a";
  const terrainEmissive = riskScore > 0.55 || isRocky ? "#b45309" : "#000000";
  const terrainEmissiveIntensity = riskScore > 0.55
    ? isEnergyCritical
      ? 0.06
      : 0.18 + riskScore * 0.15
    : isEasy
      ? 0.06
      : 0.02;
  const hazardOpacity = activePhase === 0 ? (isDustStorm ? 0.3 : 0.16) : isDustStorm ? 0.18 : 0.08;
  const dustRingOpacity = activePhase === 0 ? 0.26 : 0.18;
  const obstacleCenter = sceneData.obstacles.length
    ? {
        x: sceneData.obstacleCenter.x / sceneData.obstacles.length,
        y: sceneData.obstacleCenter.y / sceneData.obstacles.length,
      }
    : { x: 0, y: 0 };
  const startRoverDistance = Math.hypot(
    sceneData.start.x - sceneData.rover.x,
    sceneData.start.y - sceneData.rover.y
  );
  const combineStartRover = startRoverDistance < Math.max(0.7, sceneData.missionSpan * 0.12);
  const startMarkerPos = new Vector3(sceneData.start.x, 0.15, sceneData.start.y);
  const roverMarkerPos = new Vector3(sceneData.rover.x, 0.22, sceneData.rover.y);
  const goalMarkerPos = new Vector3(sceneData.goal.x, 0.15, sceneData.goal.y);
  const obstacleCentroid = new Vector3(obstacleCenter.x, 0.12, obstacleCenter.y);
  const windMarkerPos = new Vector3(
    sceneData.missionMid.x + sceneData.missionPerp.x * sceneData.missionSpan * (isHighWind ? 0.25 : 0.18),
    0.12,
    sceneData.missionMid.y + sceneData.missionPerp.y * sceneData.missionSpan * (isHighWind ? 0.25 : 0.18)
  );
  const labelLift = new Vector3(0, 0.45, 0);
  const startLabelPosition = startMarkerPos.clone().add(labelLift);
  const roverLabelPosition = roverMarkerPos.clone().add(labelLift);
  const goalLabelPosition = goalMarkerPos.clone().add(labelLift);
  const windLabelPosition = windMarkerPos.clone().add(labelLift);
  const obstacleLabelPosition = obstacleCentroid.clone().add(labelLift);
  const combinedPosition = startMarkerPos.clone().lerp(roverMarkerPos, 0.5);
  const combinedLabelPosition = combinedPosition.clone().add(labelLift);
  const dustCount = isDustStorm ? 190 : isHighWind ? 130 : isEasy ? 60 : 110;
  const dustSpeed = isDustStorm ? 0.35 : isHighWind ? 0.22 : 0.12;
  const windStreakCount = isHighWind ? 42 : 18;
  const windStreakSpeed = isHighWind ? 1.15 : 0.55;
  const windFieldCount = isHighWind ? 140 : 0;
  const windFieldSpeed = isHighWind ? 1.4 : 0.0;
  const dustSpread = terrainSize * (isDustStorm ? 1.15 : 0.95);
  const roverVisibility = isDustStorm ? 0.7 : 1;
  const roverDamping = isEnergyCritical ? 0.012 : 0.02;
  const roverTilt = isEnergyCritical ? 4.5 : 6;
  const cameraShake = isHighWind ? 0.07 : 0;

  return (
    <div className="relative h-full w-full">
      <Canvas key={scenarioId} camera={{ position: [0, 5.8, 7.4], fov: 40 }}>
      <color attach="background" args={[new Color(fogColor)]} />
      <fog attach="fog" args={[new Color(fogColor), fogNear, fogFar]} />
      <ambientLight
        intensity={ambientIntensity}
        color={isDustStorm ? "#7a3a1c" : isEnergyCritical ? "#1f2937" : "#7c3f21"}
      />
      <directionalLight
        position={[4, 6, 2]}
        intensity={sunIntensity}
        color={isDustStorm ? "#f5b26b" : isEasy ? "#ffe2b5" : "#f8d4b4"}
      />
      <directionalLight position={[-4, 4, -3]} intensity={fillIntensity} color={fillColor} />
      <pointLight
        position={[0, 4.2, 0]}
        intensity={isEasy ? 0.35 : isEnergyCritical ? 0.12 : 0.2}
        color={isEasy ? "#ffe7c2" : "#f5c18a"}
      />
      <hemisphereLight args={["#a84f2a", "#1f1210", 0.25]} />

      <gridHelper args={[10, 20, "#1f2937", "#111827"]} position={[0, 0.01, 0]} />

      <mesh key={`${scenarioId}-terrain`} rotation={[-Math.PI / 2, 0, 0]}>
        <primitive attach="geometry" object={terrainGeometry} />
        <meshStandardMaterial
          vertexColors
          flatShading
          metalness={0.1}
          roughness={isRocky ? 0.98 : 0.95}
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
        spread={dustSpread}
        height={isDustStorm ? 3.2 : 2.4}
        color={isDustStorm ? "#f59e0b" : isHighWind ? "#f0c08a" : "#e2b089"}
        speed={dustSpeed}
      />
      {isHighWind && windFieldCount > 0 && (
        <group rotation={[0, sceneData.windDirection, 0]} position={[0, 0.25, 0]}>
          <WindStreaks
            key={`${scenarioId}-wind-field-${windFieldCount}`}
            count={windFieldCount}
            spread={terrainSize * 1.6}
            length={0.8}
            speed={windFieldSpeed}
            color={windColor}
          />
        </group>
      )}

      {action === "hold_position" && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 0]}>
          <ringGeometry args={[1.8, 3.2, 32]} />
          <meshBasicMaterial color="#ef4444" transparent opacity={obstacleEmphasis} />
        </mesh>
      )}

      <mesh position={[startMarkerPos.x, startMarkerPos.y, startMarkerPos.z]}>
        <sphereGeometry args={[0.12, 32, 32]} />
        <meshStandardMaterial color="#22c55e" />
      </mesh>
      {combineStartRover ? (
        <>
          <group
            position={[
              combinedLabelPosition.x,
              combinedLabelPosition.y,
              combinedLabelPosition.z,
            ]}
          >
            <LabelBillboard text="START / ROVER" priority="medium" />
          </group>
        </>
      ) : (
        <>
          <group
            position={[
              startLabelPosition.x,
              startLabelPosition.y,
              startLabelPosition.z,
            ]}
          >
            <LabelBillboard text="START" priority="medium" />
          </group>
        </>
      )}

      <mesh position={[goalMarkerPos.x, goalMarkerPos.y, goalMarkerPos.z]}>
        <sphereGeometry args={[0.12, 32, 32]} />
        <meshStandardMaterial color="#facc15" />
      </mesh>
      <group
        position={[goalLabelPosition.x, goalLabelPosition.y, goalLabelPosition.z]}
      >
        <LabelBillboard text="GOAL" priority="high" />
      </group>

      <RoverTrail
        roverRef={roverRef}
        activePhase={activePhase}
        color={isEnergyCritical ? "#94a3b8" : "#7dd3fc"}
      />
      <RoverRig
        target={roverTarget}
        activePhase={activePhase}
        lowEnergy={isEnergyCritical}
        roverRef={roverRef}
        movementDamping={roverDamping}
        tiltScale={roverTilt}
        visibility={roverVisibility}
      />
      {!combineStartRover && (
        <>
          <group
            position={[roverLabelPosition.x, roverLabelPosition.y, roverLabelPosition.z]}
          >
            <LabelBillboard text="ROVER" priority="high" />
          </group>
        </>
      )}

      <FocusPulse
        active={activePhase === 3}
        position={roverTarget}
        color={isEnergyCritical ? "#94a3b8" : "#38bdf8"}
      />
      <FocusPulse
        active={activePhase >= 4}
        position={goalMarkerPos}
        color="#facc15"
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
          <cylinderGeometry args={[isRocky ? 0.08 : 0.06, isRocky ? 0.08 : 0.06, isRocky ? 0.18 : 0.12, 12]} />
          <meshStandardMaterial
            color="#ef4444"
            emissive="#ef4444"
            emissiveIntensity={isRocky ? 0.5 : riskScore > 0.6 ? 0.35 : activePhase === 0 ? 0.4 : 0.15}
          />
        </mesh>
      ))}

      {sceneData.obstacles.length > 0 && (
        <>
          <group
            position={[
              obstacleLabelPosition.x,
              obstacleLabelPosition.y,
              obstacleLabelPosition.z,
            ]}
          >
            <LabelBillboard
              text="Obstacle Field"
              priority="low"
              detail={`Count: ${sceneData.obstacleCount ?? sceneData.obstacles.length}`}
            />
          </group>
        </>
      )}

      <group
        ref={windRef}
        position={[windMarkerPos.x, windMarkerPos.y, windMarkerPos.z]}
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
      </group>
      <group position={[windLabelPosition.x, windLabelPosition.y, windLabelPosition.z]}>
        <LabelBillboard text="WIND" priority="low" />
      </group>

      <SceneAnimator
        activePhase={activePhase}
        plannedMaterialRef={plannedMaterialRef}
        windRef={windRef}
        windDirection={sceneData.windDirection}
      />
      <ControlsRig
        controls={controlsRef}
        focus={roverFocus}
        activePhase={activePhase}
        shakeIntensity={cameraShake}
        shakeSpeed={1.6}
      />

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
        target={[sceneData.missionMid.x, 0.2, sceneData.missionMid.y]}
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
      <div className="pointer-events-none absolute left-4 top-4 w-[180px] rounded-xl border border-slate-700/70 bg-slate-950/80 px-3 py-2 text-[10px] text-slate-200 shadow-[0_10px_30px_rgba(0,0,0,0.45)]">
        <p className="text-[10px] uppercase tracking-[0.18em] text-slate-400">Scenario Telemetry</p>
        <div className="mt-2 space-y-1 text-[10px]">
          <div className="flex items-center justify-between gap-2">
            <span className="text-slate-400">Scenario</span>
            <span className="max-w-[90px] truncate text-slate-100">{scenarioName}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-slate-400">Action</span>
            <span className="max-w-[90px] truncate text-slate-100">{action}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-slate-400">Risk</span>
            <span className="text-slate-100">{telemetryRisk.toFixed(2)}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-slate-400">Wind</span>
            <span className="text-slate-100">{telemetryWind.toFixed(1)} m/s</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-slate-400">Dust</span>
            <span className="text-slate-100">{telemetryDust.toFixed(2)}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-slate-400">Obstacles</span>
            <span className="text-slate-100">{telemetryObstacles}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-slate-400">Progress</span>
            <span className="text-slate-100">{progressPercent}%</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-slate-400">Phase</span>
            <span className="max-w-[100px] truncate text-slate-100">{telemetryPhase}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
