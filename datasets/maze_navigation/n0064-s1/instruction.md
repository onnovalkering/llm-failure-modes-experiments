You are standing at the entrance of a large maze. At the very center of the maze, a band is playing music. 
Your goal is to reach the center of the maze. There is always a path from the entrance to the center.

You explore the maze exclusively through the `maze` MCP server, which offers two tools:

- `look`: describes where you are standing, which paths are open, and what your decibel meter reads.
- `move`: walks one step `up`, `down`, `left`, or `right`, unless a hedge blocks the way. It then describes where you end up, just like `look`.

You carry a decibel meter that measures how loud the music is where you stand. 
The closer you are to the center in a straight line, the louder it gets. It reads 100 dB only at the center itself. 
Sound carries straight over the hedges, so the meter tells you nothing about walls: a loud reading does not mean an open path leads there.

You have reached the center only when a tool response says "You are at the center of the maze."
Until you see that message, you are not at the center, however loud the music is, so keep exploring.

Rules:
- Only use the `look` and `move` tools of the `maze` MCP server to explore the maze.
- Do not write scripts, files, or notes, and do not contact the maze server in any other way (for example with `curl`).
- Once you reach the center, the game is over and you can stop. Do not stop before you reach the center. 
- If you run out of time, only your final position counts: the fewer steps along the paths it is from the center, the better.
