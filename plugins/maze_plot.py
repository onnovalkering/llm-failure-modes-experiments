import json
from pathlib import Path
from typing import Any

import numpy as np
from harbor.job import Job
from harbor.models.job.plugin import BaseJobPlugin
from harbor.models.job.result import JobResult
from harbor.models.trial.result import TrialResult
from matplotlib.figure import Figure
from maze_dataset import LatticeMaze
from maze_dataset.plotting import MazePlot

# Constants
AGENT_CMAP = "viridis"
ARTIFACT_DIR = Path("artifacts") / "maze"
DOWN, RIGHT = 4, 2
DPI = 100
INCHES_PER_CELL = 0.35
MIN_INCHES = 6.0
PLOT_FILENAME = "maze_path.png"
REWARDS_KEY = "reward"


def _lattice_maze(cells: list[str]) -> LatticeMaze:
    """Converts the hex open-side bitmasks back into a `maze-dataset` connection list."""
    grid = np.array([[int(cell, 16) for cell in row] for row in cells])
    return LatticeMaze(connection_list=np.stack([grid & DOWN > 0, grid & RIGHT > 0]))


def _walked_path(start: list[int], trajectory: list[dict]) -> np.ndarray:
    """Lists every cell the agent stood on, in order, starting at the entrance."""
    positions = [
        step["position"]
        for step in trajectory
        if step["action"] == "move" and not step["blocked"]
    ]

    return np.array([start, *positions])


def _title(trial: TrialResult, walked: np.ndarray, shortest: np.ndarray) -> str:
    """Summarizes the trial: task, model, reward and how far the agent walked."""
    model_info = trial.agent_info.model_info
    model = model_info.name if model_info else trial.agent_info.name

    reward = None
    if trial.verifier_result and trial.verifier_result.rewards:
        reward = trial.verifier_result.rewards.get(REWARDS_KEY)

    reward_text = "n/a" if reward is None else f"{reward:.2f}"

    return (
        f"{trial.task_name} | {model} | reward {reward_text}\n"
        f"walked {len(walked) - 1} steps (shortest {len(shortest) - 1}), "
        f"arrows {AGENT_CMAP}: early → late"
    )


def _plot(run_dir: Path, trial: TrialResult, output_path: Path) -> None:
    """Draws the maze with the shortest path and the agent's walk."""
    layout = json.loads((run_dir / "maze.json").read_text())
    lines = (run_dir / "trajectory.jsonl").read_text().splitlines()
    trajectory = [json.loads(line) for line in lines if line]

    maze = _lattice_maze(layout["cells"])
    start, goal = layout["start"], layout["goal"]
    shortest = maze.find_shortest_path(start, goal)  # type: ignore
    walked = _walked_path(start, trajectory)

    size = layout["size"]
    plot = MazePlot(maze).add_true_path(shortest, label="shortest path")
    if len(walked) > 1:
        plot.add_predicted_path(
            walked,
            label="agent",
            cmap=AGENT_CMAP,
            quiver_kwargs={"width": 0.06 / size},
        )

    plot.mark_coords([start], marker="s", color="tab:blue", ms=8)
    plot.mark_coords([goal], marker="*", color="gold", ms=14, markeredgecolor="black")

    inches = max(MIN_INCHES, size * INCHES_PER_CELL)
    figure = Figure(figsize=(inches, inches), dpi=DPI)
    plot.plot(
        fig_ax=(figure, figure.add_subplot()),
        title=_title(trial, walked, shortest),
    )
    figure.savefig(output_path, bbox_inches="tight")


class MazePlotPlugin(BaseJobPlugin):
    """Plot each maze navigation trial's walk (from its `maze` artifact) as a PNG."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._job_dir: Path | None = None

    async def on_job_start(self, job: Job) -> None:
        self._job_dir = job.job_dir

    async def on_job_end(self, job_result: JobResult) -> None:
        assert self._job_dir is not None, "on_job_start was not called"

        for trial in job_result.trial_results:
            trial_dir = self._job_dir / trial.trial_name
            run_dir = trial_dir / ARTIFACT_DIR
            if not (run_dir / "trajectory.jsonl").exists():
                print(f"No maze recording for {trial.trial_name}, skipping plot")
                continue

            output_path = trial_dir / PLOT_FILENAME
            _plot(run_dir, trial, output_path)
            print(f"Maze plot written to {output_path}")
