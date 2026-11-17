#!/bin/bash
set -e
exec text-embeddings-router --model-id "${MODEL_ID:-BAAI/bge-m3}" --port "${PORT:-8003}" --auto-truncate