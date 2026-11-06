import json
import math
import threading
import time
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from starlette.requests import Request
from starlette.responses import JSONResponse

# Aliases
Direction = Literal["up", "down", "left", "right"]

# Constants
HERE = Path(__file__).parent
MAZE = json.loads((HERE / "maze.json").read_text())
CELLS = [[int(cell, 16) for cell in row] for row in MAZE["cells"]]
START = tuple(MAZE["start"])
GOAL = tuple(MAZE["goal"])
TOKEN = MAZE["token"]
RUN_DIR = HERE / "run"
TRAJECTORY_PATH = RUN_DIR / "trajectory.jsonl"
DIRECTIONS = {
    "up": (-1, 0, 1),
    "right": (0, 1, 2),
    "down": (1, 0, 4),
    "left": (0, -1, 8),
}

# Globals
mcp = FastMCP("maze")
lock = threading.Lock()
position = START
trajectory: list[dict] = []


def _decibels(cell: tuple[int, int]) -> float:
    """Loudness of the band, based on the straight-line distance (walls don't block sound)."""
    distance = math.dist(cell, GOAL)
    return round(100 - 20 * math.log10(1 + distance), 2)


def _open_paths(cell: tuple[int, int]) -> list[str]:
    """Lists the directions without a hedge in the way."""
    return [
        name
        for name, (_, _, bit) in DIRECTIONS.items()
        if CELLS[cell[0]][cell[1]] & bit
    ]


def _place(cell: tuple[int, int]) -> str:
    """Describes the kind of spot the player is standing on."""
    paths = _open_paths(cell)
    if len(paths) == 1:
        place = "You are in a dead end."
    elif len(paths) == 2 and set(paths) in ({"up", "down"}, {"left", "right"}):
        place = "You are on a straight path."
    elif len(paths) == 2:
        place = "You are at a bend in the path."
    elif len(paths) == 3:
        place = "You are at a fork in the path."
    else:
        place = "You are at a crossroads."

    if cell == START:
        place += " The gate you entered through is here, locked shut."

    return place


def _describe(
    opening: str,
    cell: tuple[int, int],
    previous: tuple[int, int] | None,
) -> str:
    """Renders the text-adventure style response for the player."""
    reading = f"Decibel meter: {_decibels(cell):.2f} dB"
    if previous is not None:
        before, now = _decibels(previous), _decibels(cell)
        trend = "louder" if now > before else "quieter" if now < before else "unchanged"
        reading += f" ({trend})"

    lines = [opening]
    if cell == GOAL:
        lines.append(
            "You are at the center of the maze. The band is playing right in front of you."
        )
    else:
        lines.append(_place(cell))
        lines.append(f"Open paths: {', '.join(_open_paths(cell))}.")

    lines.append(f"{reading}.")
    return "\n".join(lines)


def _session() -> str | None:
    """Returns the MCP session id, which helps spot clients other than the agent."""
    return get_http_headers(include={"mcp-session-id"}).get("mcp-session-id")


def _start_recording() -> None:
    """Writes the maze layout (without the token) next to an empty trajectory."""
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    layout = {key: value for key, value in MAZE.items() if key != "token"}

    maze_file = RUN_DIR / "maze.json"
    maze_file.write_text(json.dumps(layout, indent=2))

    TRAJECTORY_PATH.touch()


def _record(action: str, direction: str | None, blocked: bool) -> None:
    """Appends a step to the trajectory, for the verifier and the run recording."""
    step = {
        "action": action,
        "direction": direction,
        "blocked": blocked,
        "position": list(position),
        "session": _session(),
        "time": time.time(),
    }

    trajectory.append(step)
    with TRAJECTORY_PATH.open("a") as f:
        f.write(json.dumps(step) + "\n")


@mcp.tool
def look() -> str:
    """Look around: describes where you stand, which paths are open, and the decibel meter reading."""
    with lock:
        _record("look", None, False)
        return _describe("You look around.", position, None)


@mcp.tool
def move(direction: Direction) -> str:
    """Walk one step ("up", "down", "left" or "right"), if no hedge blocks the way."""
    global position

    with lock:
        if position == GOAL:
            _record("move", direction, True)
            return _describe(
                "You already reached the center of the maze. There is no need to go anywhere.",
                position,
                None,
            )

        row, col = position
        dr, dc, bit = DIRECTIONS[direction]
        if not CELLS[row][col] & bit:
            _record("move", direction, True)
            return _describe(
                f"You bump into a hedge. You can't go {direction} from here.",
                position,
                position,
            )

        previous, position = position, (row + dr, col + dc)
        _record("move", direction, False)

        opening = f"You walk {direction}."
        if position == GOAL:
            opening += " You step into a clearing. You made it!"

        return _describe(opening, position, previous)


@mcp.custom_route("/state", methods=["GET"])
async def state(request: Request) -> JSONResponse:
    """Exposes the game state to the verifier (token protected, so the agent can't peek)."""
    if request.headers.get("authorization") != f"Bearer {TOKEN}":
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    with lock:
        return JSONResponse(
            {
                "position": list(position),
                "reached_center": position == GOAL,
                "trajectory": list(trajectory),
            }
        )


if __name__ == "__main__":
    _start_recording()
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
