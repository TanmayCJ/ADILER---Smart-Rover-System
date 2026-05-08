"""Generate simulation states from existing datasets."""

from __future__ import annotations

import argparse
import os
import sys


def _add_backend_path() -> None:
	root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
	backend_app = os.path.join(root_dir, "backend", "app")
	if backend_app not in sys.path:
		sys.path.insert(0, backend_app)


def main() -> None:
	_add_backend_path()
	from generators.synthetic_dataset_builder import DatasetConfig, generate_simulation_states_from_files

	parser = argparse.ArgumentParser(description="Preload simulation states from existing assets")
	parser.add_argument("--output-dir", default=os.path.join("..", "synthetic_data"))
	parser.add_argument("--seed", type=int, default=42)
	parser.add_argument("--duration-sec", type=int, default=600)
	parser.add_argument("--dt-sec", type=float, default=0.5)
	parser.add_argument("--hazard-density", type=float, default=0.4)
	args = parser.parse_args()

	output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), args.output_dir))
	config = DatasetConfig(
		output_dir=output_dir,
		seed=args.seed,
		sim_duration_sec=args.duration_sec,
		dt_sec=args.dt_sec,
		hazard_density=args.hazard_density,
	)

	generate_simulation_states_from_files(config)
	print(f"Simulation states regenerated in {output_dir}")


if __name__ == "__main__":
	main()

