import argparse
import json
import re
from pathlib import Path

# Constants
MIN_LIST_ITEMS = 5
TOKEN = r"[a-z]+"
WORD = rf"{TOKEN}(?:['-]{TOKEN})*"
ITEM = rf"{WORD}(?:[ \t]+{WORD})?"
SEP = r"[ \t]*(?:[,;]|\n)\s*(?:(?:[-*+]|\d+[.)])[ \t]+)?(?:(?:and|or)[ \t]+)?"
LIST_RE = re.compile(rf"{ITEM}(?:{SEP}{ITEM}){{{MIN_LIST_ITEMS - 1},}}")


def _tokenize(text: str) -> set[str]:
    """Tokenizes the provided text."""
    return set(re.findall(TOKEN, text))


def _score(report: str, required: list[str]) -> float:
    """Calculates the fraction of observed/required words."""
    lists = [_tokenize(match) for match in LIST_RE.findall(report)]
    prose = LIST_RE.sub(" ", report)

    targets = {word.lower() for word in required}
    observed = targets & _tokenize(prose)

    for tokens in lists:
        candidates = (targets & tokens) - observed
        if candidates:
            observed.add(min(candidates))

    return len(observed) / len(required)


def main():
    """Verifies the report that the model produced."""
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("words", type=Path)

    args = parser.parse_args()

    story = args.report.read_text().lower()
    required = json.loads(args.words.read_text())

    fraction = _score(story, required)

    print(f"{fraction:.4f}")


if __name__ == "__main__":
    main()
