# LLM failure modes experiments

```
export PYTHONPATH=.

harbor run \
  --agent opencode \
  --model openrouter/anthropic/claude-haiku-5.5 \
  --model openrouter/anthropic/claude-sonnet-5.5 \
  --model openrouter/anthropic/claude-opus-5.5 \
  --path datasets/instruction_count \
  --n-concurrent 7  \
  --plugin plugins.reward_matrix:RewardMatrixPlugin \
  --ak 'opencode_config={"snapshot": false}'
```
