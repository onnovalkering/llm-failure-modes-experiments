import json
import re
import sys
from pathlib import Path

MIN_LIST_ITEMS = 5
TOKEN = r"[a-z]+"
WORD = rf"{TOKEN}(?:['-]{TOKEN})*"
ITEM = rf"{WORD}(?:[ \t]+{WORD})?"
SEP = r"[ \t]*(?:[,;]|\n)\s*(?:(?:[-*+]|\d+[.)])[ \t]+)?(?:(?:and|or)[ \t]+)?"
LIST_RE = re.compile(rf"{ITEM}(?:{SEP}{ITEM}){{{MIN_LIST_ITEMS - 1},}}")


def tokenize(text: str) -> set[str]:
    """Tokenizes the provided text."""
    return set(re.findall(TOKEN, text))


def score(report: str, required: list[str]) -> float:
    """Calculates the fraction of observed/required words."""
    lists = [tokenize(match) for match in LIST_RE.findall(report)]
    prose = LIST_RE.sub(" ", report)

    targets = {word.lower() for word in required}
    observed = targets & tokenize(prose)

    for tokens in lists:
        candidates = (targets & tokens) - observed
        if candidates:
            observed.add(min(candidates))

    return len(observed) / len(required)


def main():
    """Verifies the report that the model produced."""
    report_path, words_path = Path(sys.argv[1]), Path(sys.argv[2])

    story = report_path.read_text().lower()
    required = json.loads(words_path.read_text())

    fraction = score(story, required)

    print(f"{fraction:.4f}")


if __name__ == "__main__":
    main()
