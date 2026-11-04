import argparse
import json
import random
import shutil
from pathlib import Path

# Constants
HERE = Path(__file__).parent
TEMPLATE_PATH = HERE / "template"
WORDS_FILE = HERE / "assets" / "google-10000-english-20k.txt"


def sample_words(vocabulary: list[str], count: int, seed: int) -> list[str]:
    """..."""
    return random.Random(seed).sample(vocabulary, count)


def render_task(output_dir: Path, words: list[str], agent_timeout: int) -> None:
    """..."""
    shutil.copytree(TEMPLATE_PATH, output_dir, dirs_exist_ok=True)

    instructions = "\n".join(f"Use the word {word!r} in the story." for word in words)

    instructions_path = output_dir / "instruction.md"
    instructions_render = instructions_path.read_text().format(
        instructions=instructions
    )
    instructions_path.write_text(instructions_render)

    task_config_path = output_dir / "task.toml"
    task_config_render = task_config_path.read_text().format(
        agent_timeout=agent_timeout
    )
    task_config_path.write_text(task_config_render)

    expected_words_path = output_dir / "tests" / "expected_words.json"
    expected_words_render = json.dumps(words, indent=2)
    expected_words_path.write_text(expected_words_render)


def main():
    """..."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts", type=int, nargs="+", required=True)
    parser.add_argument("--seeds", type=int, nargs="*", default=[42])
    parser.add_argument("--out", type=Path, default=Path("datasets/instruction_count"))

    args = parser.parse_args()

    vocabulary = WORDS_FILE.read_text().split()
    for count in args.counts:
        if count > len(vocabulary):
            raise ValueError(f"Provided count exceeds vocabulary size.")

        for seed in args.seeds:
            words = sample_words(vocabulary, count, seed)
            agent_timeout = 60 * 5 + count

            render_task(args.out / f"n{count:04d}-s{seed}", words, agent_timeout)


if __name__ == "__main__":
    main()
