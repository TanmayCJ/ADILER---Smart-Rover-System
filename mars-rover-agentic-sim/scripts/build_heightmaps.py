"""Generate terrain tiles and heightmaps only."""

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
	from generators.synthetic_dataset_builder import DatasetConfig, build_terrain_assets
	from generators.terrain_generator import write_terrain_assets

	parser = argparse.ArgumentParser(description="Generate terrain tiles and heightmaps")
	parser.add_argument("--output-dir", default=os.path.join("..", "synthetic_data"))
	parser.add_argument("--seed", type=int, default=42)
	parser.add_argument("--rows", type=int, default=2)
	parser.add_argument("--cols", type=int, default=2)
	parser.add_argument("--heightmap-size", type=int, default=64)
	parser.add_argument("--meters-per-pixel", type=float, default=2.0)
	parser.add_argument("--terrain-complexity", type=float, default=0.6)
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
	)

	tiles, heightmaps, traversability_maps = build_terrain_assets(config)
	write_terrain_assets(tiles, heightmaps, traversability_maps, config.output_dir)
	print(f"Generated {len(tiles)} terrain tiles in {output_dir}")


if __name__ == "__main__":
	main()

