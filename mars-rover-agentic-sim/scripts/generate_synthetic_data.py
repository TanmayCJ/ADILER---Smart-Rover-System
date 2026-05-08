"""Generate full synthetic dataset for the Mars rover simulation."""

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
	from generators.synthetic_dataset_builder import DatasetConfig, build_full_dataset

	parser = argparse.ArgumentParser(description="Generate synthetic Mars datasets")
	parser.add_argument("--output-dir", default=os.path.join("..", "synthetic_data"))
	parser.add_argument("--seed", type=int, default=42)
	parser.add_argument("--rows", type=int, default=2)
	parser.add_argument("--cols", type=int, default=2)
	parser.add_argument("--heightmap-size", type=int, default=64)
	parser.add_argument("--meters-per-pixel", type=float, default=2.0)
	parser.add_argument("--terrain-complexity", type=float, default=0.6)
	parser.add_argument("--hazard-density", type=float, default=0.4)
	parser.add_argument("--wind-intensity", type=float, default=0.6)
	parser.add_argument("--duration-sec", type=int, default=600)
	parser.add_argument("--dt-sec", type=float, default=0.5)
	parser.add_argument("--missions-per-tile", type=int, default=1)
	args = parser.parse_args()

	output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), args.output_dir))
	tile_size_m = args.heightmap_size * args.meters_per_pixel

	config = DatasetConfig(
		output_dir=output_dir,
		seed=args.seed,
		tile_rows=args.rows,
		tile_cols=args.cols,
		heightmap_size=args.heightmap_size,
		meters_per_pixel=args.meters_per_pixel,
		tile_size_m=tile_size_m,
		terrain_complexity=args.terrain_complexity,
		hazard_density=args.hazard_density,
		wind_intensity=args.wind_intensity,
		sim_duration_sec=args.duration_sec,
		dt_sec=args.dt_sec,
		missions_per_tile=args.missions_per_tile,
	)

	summary = build_full_dataset(config)
	print(f"Generated dataset in {output_dir}")
	print(f"Tiles: {summary['tiles']}, Missions: {summary['missions']}, Scenarios: {summary['scenarios']}")


if __name__ == "__main__":
	main()

