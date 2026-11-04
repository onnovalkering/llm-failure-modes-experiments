import argparse
import json
import random
import shutil
from pathlib import Path

# Constants
HERE = Path(__file__).parent
TEMPLATE_PATH = HERE / "template"
WORDS_FILE = HERE / "assets" / "google-10000-english-20k-filtered.txt"
INSTRUCTION_SENTENCE = "Use the word {word!r} naturally and at least once in the report."


def _sample_words(vocabulary: list[str], count: int, seed: int) -> list[str]:
    """Takes a random sample of words from the vocabulary."""
    return random.Random(seed).sample(vocabulary, count)

def _generate_instructions(words: list[str]) -> str:
    """Generates the instruction set, one per word."""
    return "\n".join(INSTRUCTION_SENTENCE.format(word=word) for word in words)


def _render_task(output_dir: Path, words: list[str], agent_timeout: int) -> None:
    """Renders the template files and assets needed for the Harbor experiment."""
    shutil.copytree(TEMPLATE_PATH, output_dir, dirs_exist_ok=True)
    instructions = _generate_instructions(words)

    # Render the `instructions.md` file.
    instructions_path = output_dir / "instruction.md"
    instructions_render = instructions_path.read_text().format(
        instructions=instructions
    )
    instructions_path.write_text(instructions_render)

    # Render the `task.toml` file.
    task_config_path = output_dir / "task.toml"
    task_config_render = task_config_path.read_text().format(
        agent_timeout=agent_timeout
    )
    task_config_path.write_text(task_config_render)

    # Dump expected words to `expected_words.json`.
    expected_words_path = output_dir / "tests" / "expected_words.json"
    expected_words_render = json.dumps(words, indent=2)
    expected_words_path.write_text(expected_words_render)


def main():
    """Generates Harbor experiments from the `instruction_count` template."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts", type=int, nargs="+", required=True)
    parser.add_argument("--seeds", type=int, nargs="*", default=[42])
    parser.add_argument("--out", type=Path, default=Path("datasets/instruction_count"))

    args = parser.parse_args()

    vocabulary = WORDS_FILE.read_text().split()
    for count in args.counts:
        if count > len(vocabulary):
            raise ValueError("Provided count exceeds vocabulary size.")

        for seed in args.seeds:
            words = _sample_words(vocabulary, count, seed)

            # Timeout: five minutes + one minute for every 250 words.
            agent_timeout = 300 + ((count // 250) * 60)
            _render_task(args.out / f"n{count:04d}-s{seed}", words, agent_timeout)


if __name__ == "__main__":
    main()
