#!/bin/bash
set -e
MODEL_ID="${MODEL_ID:-Qwen/Qwen2.5-1.5B-Instruct}"
PORT="${PORT:-8001}"
GPU_MEMORY_UTIL="${GPU_MEMORY_UTIL:-0.4}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
QUANTIZATION="${QUANTIZATION:-}"

ARGS=(--model "$MODEL_ID" --port "$PORT" --host 0.0.0.0 --gpu-memory-utilization "$GPU_MEMORY_UTIL" --max-model-len "$MAX_MODEL_LEN" --served-model-name "$MODEL_ID")
[ -n "$QUANTIZATION" ] && ARGS+=(--quantization "$QUANTIZATION")
exec python3 -m vllm.entrypoints.openai.api_server "${ARGS[@]}"