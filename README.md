# LLM failure modes experiments

...

## Instruction count
...

```
python ./experiments/instruction_count/generate.py \
  --counts 32 64 128 256 512 768 1024 \ 
  --seeds 0 1 2
```

### Experiment validation
...

```
PYTHONPATH=. harbor run \
  --agent opencode \
  --model openrouter/anthropic/claude-haiku-5.5 \
  --path datasets/instruction_count \
  --n-concurrent 4  \
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

### Experiment validation
...

```
PYTHONPATH=. harbor run \
  --agent opencode \
  --model openrouter/anthropic/claude-haiku-5.5 \
  --path datasets/maze_navigation \
  --n-concurrent 4 \
  --plugin plugins.reward_matrix:RewardMatrixPlugin \
  --plugin plugins.maze_plot:MazePlotPlugin \
  --ak 'opencode_config={"snapshot": false}'
```

### Experiment 
...

```
PYTHONPATH=. harbor run \
  --agent opencode \
  --model openrouter/google/gemma-4-26b-a4b-it \
  --model openrouter/openai/gpt-oss-20b \
  --model openrouter/qwen/qwen3.5-35b-a3b \
  --model openrouter/mistralai/ministral-8b-2512 \
  --path datasets/maze_navigation \
  --n-concurrent 4 \
  --plugin plugins.reward_matrix:RewardMatrixPlugin \
  --plugin plugins.maze_plot:MazePlotPlugin \
  --ak 'opencode_config={"snapshot": false}'
```
