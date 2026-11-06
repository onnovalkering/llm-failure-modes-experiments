#!/usr/bin/env bash

python3 /tests/verify.py /tests/maze.json http://maze:8000 --logs /logs/verifier >/logs/verifier/reward.json
