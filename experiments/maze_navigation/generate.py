import argparse
import json
import random
import shutil
from collections import deque
from pathlib import Path

import numpy as np
from maze_dataset.generation import LatticeMazeGenerators

# Aliases
Cell: type = tuple[int, int]

# Constants
DIRECTIONS = {
    "up": (-1, 0, 1),
    "right": (0, 1, 2),
    "down": (1, 0, 4),
    "left": (0, -1, 8),
}
GENERATOR = LatticeMazeGenerators.gen_dfs
GROWTH = 1.25
HERE = Path(__file__).parent
MAX_ATTEMPTS = 200
TEMPLATE_PATH = HERE / "template"


def _odd(value: int) -> int:
    """Rounds up to the nearest odd number, so the maze has a single center cell."""
    return value if value % 2 else value + 1


def _carve_maze(size: int, rng: random.Random) -> list[list[int]]:
    """Carves a perfect maze with `maze-dataset` and converts it to open-side bitmasks."""
    random.seed(rng.getrandbits(32))
    np.random.seed(rng.getrandbits(32))

    # Connection list: [0, row, col] links a cell to the one below, [1, row, col] to the right.
    connections = GENERATOR((size, size)).connection_list

    cells = [[0] * size for _ in range(size)]
    for row, col in zip(*np.nonzero(connections[0])):
        cells[row][col] |= DIRECTIONS["down"][2]
        cells[row + 1][col] |= DIRECTIONS["up"][2]

    for row, col in zip(*np.nonzero(connections[1])):
        cells[row][col] |= DIRECTIONS["right"][2]
        cells[row][col + 1] |= DIRECTIONS["left"][2]

    return cells


def _distances(cells: list[list[int]], origin: Cell) -> list[list[int]]:
    """Computes the walking distance from the origin to every cell (BFS)."""
    size = len(cells)
    distances = [[-1] * size for _ in range(size)]
    distances[origin[0]][origin[1]] = 0
    queue = deque([origin])

    while queue:
        row, col = queue.popleft()
        for dr, dc, bit in DIRECTIONS.values():
            next_row, next_col = row + dr, col + dc
            if cells[row][col] & bit and distances[next_row][next_col] < 0:
                distances[next_row][next_col] = distances[row][col] + 1
                queue.append((next_row, next_col))

    return distances


def _boundary(size: int) -> list[Cell]:
    """Lists all cells on the outer edge of the maze."""
    edge = {size - 1, 0}
    return [
        (row, col)
        for row in range(size)
        for col in range(size)
        if row in edge or col in edge
    ]


def _next_size(size: int, too_small: int, too_large: int | None) -> int:
    """Grows geometrically until a maze was too large, then bisects between the bounds."""
    if too_large is None:
        return _odd(max(size + 2, int(size * GROWTH)))

    return max(too_small + 2, _odd((too_small + too_large) // 2))


def _generate_maze(steps: int, seed: int) -> dict:
    """Generates a maze for the number of specified steps from start to finish point."""
    rng = random.Random(f"maze-{steps}-{seed}")
    size, too_small, too_large = 3, 1, None

    for _ in range(MAX_ATTEMPTS):
        goal = (size // 2, size // 2)
        cells = _carve_maze(size, rng)
        distances = _distances(cells, goal)
        edge = {cell: distances[cell[0]][cell[1]] for cell in _boundary(size)}

        starts = [cell for cell, distance in edge.items() if distance == steps]
        if starts:
            start = rng.choice(starts)
            token = random.Random(f"token-{steps}-{seed}").getrandbits(128)
            return {
                "steps": steps,
                "seed": seed,
                "size": size,
                "start": list(start),
                "goal": list(goal),
                "token": f"{token:032x}",
                "cells": ["".join(f"{cell:x}" for cell in row) for row in cells],
            }

        # Every edge cell is too close or too far, otherwise retry this size with a new maze.
        if max(edge.values()) < steps:
            too_small = max(too_small, size)
            size = _next_size(size, too_small, too_large)
        elif min(edge.values()) > steps:
            too_large = size if too_large is None else min(too_large, size)
            size = _next_size(size, too_small, too_large)

    raise RuntimeError(f"Could not generate a maze with {steps} steps.")


def _render_task(output_dir: Path, maze: dict, agent_timeout: int) -> None:
    """Renders the template files and assets needed for the Harbor experiment."""
    shutil.copytree(TEMPLATE_PATH, output_dir, dirs_exist_ok=True)

    # Render the `task.toml` file.
    task_config_path = output_dir / "task.toml"
    task_config_render = task_config_path.read_text().format(
        agent_timeout=agent_timeout
    )
    task_config_path.write_text(task_config_render)

    # Dump the maze for the MCP server (hidden sidecar) and for the verifier.
    maze_render = json.dumps(maze, indent=2)

    mcp_server_maze_file = output_dir / "environment" / "maze-server" / "maze.json"
    mcp_server_maze_file.write_text(maze_render)

    verifier_maze_file = output_dir / "tests" / "maze.json"
    verifier_maze_file.write_text(maze_render)


def main():
    """Generates Harbor experiments from the `maze_navigation` template."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, nargs="+", required=True)
    parser.add_argument("--seeds", type=int, nargs="*", default=[42])
    parser.add_argument("--out", type=Path, default=Path("datasets/maze_navigation"))

    args = parser.parse_args()

    for steps in args.steps:
        if steps < 1:
            raise ValueError("Provided steps must be positive.")

        for seed in args.seeds:
            maze = _generate_maze(steps, seed)

            # Timeout: ten minutes + ten seconds for every step on the shortest path.
            agent_timeout = 600 + (steps * 10)
            _render_task(args.out / f"n{steps:04d}-s{seed}", maze, agent_timeout)


if __name__ == "__main__":
    main()
