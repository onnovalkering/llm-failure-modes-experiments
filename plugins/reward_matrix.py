import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, cast

from harbor.job import Job
from harbor.models.job.plugin import BaseJobPlugin
from harbor.models.job.result import JobResult

# Constants
REWARDS_FILENAME = "rewards.csv"
REWARDS_KEY = "reward"


class RewardMatrixPlugin(BaseJobPlugin):
    """Write a model x task reward matrix as CSV when a job finishes."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._output_path: Path | None = None

    async def on_job_start(self, job: Job) -> None:
        self._output_path = job.job_dir / REWARDS_FILENAME

    async def on_job_end(self, job_result: JobResult) -> None:
        assert self._output_path is not None, "on_job_start was not called"

        tasks = cast(set[str], set())
        rewards = cast(
            dict[str, dict[str, list[float]]],
            defaultdict(lambda: defaultdict(list)),
        )

        for trial in job_result.trial_results:
            model_info = trial.agent_info.model_info
            model = model_info.name if model_info else trial.agent_info.name

            tasks.add(trial.task_name)

            # Touch the cell so models/tasks without any reward still show up.
            cell = rewards[model][trial.task_name]
            verifier_result = trial.verifier_result
            if verifier_result and verifier_result.rewards:
                reward = verifier_result.rewards.get(REWARDS_KEY)
                if reward is not None:
                    cell.append(reward)

        columns = sorted(tasks)
        with self._output_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["model", *columns])

            for model in sorted(rewards):
                row = rewards[model]
                writer.writerow(
                    [model, *(mean(row[t]) if row[t] else "" for t in columns)]
                )

        print(f"Reward matrix written to {self._output_path}")
