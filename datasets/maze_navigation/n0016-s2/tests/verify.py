import argparse
import json
import math
import time
import urllib.request
from collections import deque
from pathlib import Path

# Aliases
Cell: type = tuple[int, int]

# Constants
DIRECTIONS = {
    "up": (-1, 0, 1),
    "right": (0, 1, 2),
    "down": (1, 0, 4),
    "left": (0, -1, 8),
}
FETCH_ATTEMPTS = 5
FETCH_BACKOFF_SEC = 2.0


def _fetch_state(server: str, token: str) -> dict:
    """Fetches the game state from the maze server, failing loudly if it is unreachable."""
    request = urllib.request.Request(
        f"{server.rstrip('/')}/state",
        headers={"Authorization": f"Bearer {token}"},
    )

    for attempt in range(FETCH_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return json.load(response)
        except OSError:
            if attempt == FETCH_ATTEMPTS - 1:
                raise

            time.sleep(FETCH_BACKOFF_SEC)

    raise AssertionError("unreachable")


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


def _decibels(cell: Cell, goal: Cell) -> float:
    """Same meter as the maze server: straight-line distance, walls don't block sound."""
    return round(100 - 20 * math.log10(1 + math.dist(cell, goal)), 2)


def _render_ascii(
    cells: list[list[int]],
    start: Cell,
    goal: Cell,
    final: Cell,
    visited: set[Cell],
) -> str:
    """Draws the maze with the visited cells, for eyeballing a run."""
    size = len(cells)
    canvas = [["#"] * (2 * size + 1) for _ in range(2 * size + 1)]
    for row in range(size):
        for col in range(size):
            canvas[2 * row + 1][2 * col + 1] = "." if (row, col) in visited else " "

            if cells[row][col] & DIRECTIONS["right"][2]:
                canvas[2 * row + 1][2 * col + 2] = " "

            if cells[row][col] & DIRECTIONS["down"][2]:
                canvas[2 * row + 2][2 * col + 1] = " "

    for (row, col), marker in ((start, "S"), (goal, "G"), (final, "@")):
        canvas[2 * row + 1][2 * col + 1] = marker

    return "\n".join("".join(line) for line in canvas) + "\n"


def _score(
    cells: list[list[int]],
    start: Cell,
    goal: Cell,
    final: Cell,
    trajectory: list[dict],
    visited: set[Cell],
) -> dict:
    """Grades the final position, plus some diagnostics about the exploration."""
    distances = _distances(cells, goal)
    shortest_path = distances[start[0]][start[1]]

    moves = [step for step in trajectory if step["action"] == "move"]
    walked = [step for step in moves if not step["blocked"]]

    final_distance = distances[final[0]][final[1]]
    best_distance = min(distances[row][col] for row, col in visited)
    reached_center = final == goal

    # Steps away from the center, scaled so the center scores 1.0 and the entrance (or further) 0.0.
    # Walking distance, not decibels: a loud dead-end pocket behind a hedge isn't "close".
    reward = max(0.0, 1 - final_distance / shortest_path)

    start_db, final_db = _decibels(start, goal), _decibels(final, goal)
    db_score = min(1.0, max(0.0, (final_db - start_db) / (100 - start_db)))

    return {
        "reward": round(reward, 4),
        "db_score": round(db_score, 4),
        "reached_center": int(reached_center),
        "final_path_distance": final_distance,
        "best_path_distance": best_distance,
        "shortest_path": shortest_path,
        "final_db": final_db,
        "moves": len(walked),
        "blocked_moves": len(moves) - len(walked),
        "looks": len(trajectory) - len(moves),
        "unique_cells": len(visited),
        "revisits": len(walked) - (len(visited) - 1),
        "sessions": len({step["session"] for step in trajectory if step["session"]}),
    }


def main():
    """Verifies how close the agent got to the center of the maze."""
    parser = argparse.ArgumentParser()
    parser.add_argument("maze", type=Path)
    parser.add_argument("server", type=str)
    parser.add_argument("--logs", type=Path, default=Path("/logs/verifier"))

    args = parser.parse_args()

    maze = json.loads(args.maze.read_text())
    state = _fetch_state(args.server, maze["token"])

    cells = [[int(cell, 16) for cell in row] for row in maze["cells"]]
    start, goal = tuple(maze["start"]), tuple(maze["goal"])
    final = tuple(state["position"])
    trajectory = state["trajectory"]
    visited = {start} | {tuple(step["position"]) for step in trajectory}

    result = _score(cells, start, goal, final, trajectory, visited)

    # Keep the scores around for analysis; the full trajectory is collected as an artifact.
    args.logs.mkdir(parents=True, exist_ok=True)

    metrics_file = args.logs / "metrics.json"
    metrics_file.write_text(json.dumps(result, indent=2))

    maze_file = args.logs / "maze.txt"
    maze_file.write_text(_render_ascii(cells, start, goal, final, visited))

    # Harbor treats every key in `reward.json` as a reward, so only report the reward itself.
    print(json.dumps({"reward": result["reward"]}))


if __name__ == "__main__":
    main()
