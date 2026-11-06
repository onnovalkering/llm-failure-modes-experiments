# LLM failure modes experiments

...

## Instruction count
...

```
python ./experiments/instruction_count/generate.py \
  --counts 32 64 128 256 512 768 1024 \ 
  --seeds 0 1 2
```

```
PYTHONPATH=. harbor run \
  --agent opencode \
  --model openrouter/anthropic/claude-haiku-5.5 \
  --model openrouter/anthropic/claude-sonnet-5.5 \
  --model openrouter/anthropic/claude-opus-5.5 \
  --path datasets/instruction_count \
  --n-concurrent 7  \
  --plugin plugins.reward_matrix:RewardMatrixPlugin \
  --ak 'opencode_config={"snapshot": false}'
```

## Maze navigation
...

```
python ./experiments/maze_navigation/generate.py \
  --steps 4 8 12 16 24 32 64 \
  --seeds 0 1 2
```

```
PYTHONPATH=. harbor run \
  --agent opencode \
  --model openrouter/anthropic/claude-haiku-5.5 \
  --model openrouter/anthropic/claude-sonnet-5.5 \
  --model openrouter/anthropic/claude-opus-5.5 \
  --path datasets/maze_navigation \
  --n-concurrent 7  \
  --plugin plugins.reward_matrix:RewardMatrixPlugin \
  --plugin plugins.maze_plot:MazePlotPlugin \
  --ak 'opencode_config={"snapshot": false}'
```
