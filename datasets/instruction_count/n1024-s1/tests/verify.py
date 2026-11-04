import json
import re
import sys
from pathlib import Path


def score(story: str, required: list[str]) -> float:
    """..."""
    tokens = set(re.findall(r"[a-z]+", story.lower()))
    observed = sum(1 for word in required if word.lower() in tokens)

    return observed / len(required)


def main():
    """..."""
    story_path, words_path = Path(sys.argv[1]), Path(sys.argv[2])

    story = story_path.read_text()
    required = json.loads(words_path.read_text())

    fraction = score(story, required)

    print(f"{fraction:.4f}")


if __name__ == "__main__":
    main()
