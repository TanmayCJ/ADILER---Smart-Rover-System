type ScenarioSelectorProps = {
  scenarios: string[];
  selected: string;
  onSelect: (scenario: string) => void;
};

export default function ScenarioSelector({
  scenarios,
  selected,
  onSelect,
}: ScenarioSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {scenarios.map((scenario) => (
        <button
          key={scenario}
          type="button"
          onClick={() => onSelect(scenario)}
          className={`rounded-full border px-4 py-2 text-xs uppercase tracking-[0.2em] transition ${
            selected === scenario
              ? "border-orange-300 bg-orange-500/20 text-orange-200"
              : "border-slate-600 bg-slate-900/50 text-slate-300 hover:border-slate-400"
          }`}
        >
          {scenario.replace(/_/g, " ")}
        </button>
      ))}
    </div>
  );
}
