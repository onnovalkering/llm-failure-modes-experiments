import shlex
import tempfile
from pathlib import Path
from typing import override

from harbor.agents.installed.base import with_prompt_template
from harbor.agents.installed.copilot_cli import CopilotCli
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

# Constants
_PROMPT_PATH = "/tmp/harbor-instruction.md"


class CopilotCliStdin(CopilotCli):
    """Avoids the Linux kernel 128 KiB per argument limit (MAX_ARG_STRLEN) for long prompts."""

    @override
    @with_prompt_template
    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ):
        """..."""
        token = self._get_env("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
        env = {"COPILOT_GITHUB_TOKEN": token} if token is not None else {}

        await self._restore_session_state(environment, env)
        await self._upload_instruction(instruction, environment)

        model_flag = ""
        if self.model_name:
            model_flag = f"--model={shlex.quote(self.model_name.rsplit('/', 1)[-1])}"
            web_flag = "--deny-tool web_fetch --deny-tool web_search"

            try:
                await self.exec_as_agent(
                    environment,
                    command=(
                        'set -o pipefail; export PATH="$HOME/.local/bin:$PATH"; '
                        f"copilot --yolo {web_flag} {model_flag} "
                        f"{self.build_cli_flags()} {self._build_mcp_config_flag() or ''} "
                        "--output-format=json "
                        # Prompt arrives on stdin, replacing the parent's --prompt=... and </dev/null.
                        f"< {_PROMPT_PATH} 2>&1 | stdbuf -oL tee {self._TRAJECTORY_PATH}"
                    ),
                    env=env,
                )
            finally:
                await self.exec_as_agent(
                    environment,
                    command=f"cat {self._TRAJECTORY_PATH} > {self._OUTPUT_PATH} 2>/dev/null || true",
                )
                await self._save_session_state(environment, env)

    @staticmethod
    async def _upload_instruction(
        instruction: str, environment: BaseEnvironment
    ) -> None:
        """..."""
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "instruction.md"
            local.write_text(instruction)
            await environment.upload_file(local, _PROMPT_PATH)
