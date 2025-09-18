import json
import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import logging
from time import time
from typing import List, Dict
from collections import Counter
import math


app = Flask(__name__)


def require_env(var_name: str) -> str:
    value = os.environ.get(var_name)
    if not value:
        raise EnvironmentError(f"{var_name} environment variable is required")
    return value


GITHUB_TOKEN = require_env("GITHUB_TOKEN")
GIST_ID = require_env("GIST_ID")
GIST_FILENAME = "mixa_memories.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
)

CACHE_TTL = 60  # seconds
_cache: Dict[str, any] = {"memories": None, "timestamp": 0}
MEMORY_LIMIT = 100


# Load memory list from GitHub Gist with in-memory cache
def get_gist_content(force_refresh: bool = False):
    if (
        not force_refresh
        and _cache["memories"] is not None
        and time() - _cache["timestamp"] < CACHE_TTL
    ):
        return _cache["memories"]

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/gists/{GIST_ID}"
    response = requests.get(url, headers=headers)

    memories = []
    if response.status_code == 200:
        gist_data = response.json()
        files = gist_data.get("files", {})
        if GIST_FILENAME in files:
            file_content = files[GIST_FILENAME]["content"]
            try:
                memories = json.loads(file_content)
            except json.JSONDecodeError:
                memories = []

    _cache["memories"] = memories
    _cache["timestamp"] = time()
    return memories


# Update the Gist with new memory list
def update_gist_content(memories):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "files": {
            GIST_FILENAME: {
                "content": json.dumps(memories, indent=2, ensure_ascii=False)
            }
        }
    }
    response = requests.patch(
        f"https://api.github.com/gists/{GIST_ID}",
        headers=headers,
        data=json.dumps(data),
    )
    if response.status_code == 200:
        _cache["memories"] = memories
        _cache["timestamp"] = time()
        return True
    return False


def prune_memories(memories: List[Dict], limit: int = MEMORY_LIMIT) -> List[Dict]:
    if len(memories) <= limit:
        return memories

    excess = len(memories) - (limit - 1)
    old_memories = memories[:excess]
    summary_text = " | ".join(m.get("summary", "") for m in old_memories)
    summary_memory = {
        "id": "1",
        "summary": f"Summary of earlier memories: {summary_text}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    remaining = [summary_memory] + memories[excess:]
    for idx, mem in enumerate(remaining, start=1):
        mem["id"] = str(idx)
    return remaining


def get_relevant_memories(query: str, k: int = 5) -> List[Dict]:
    memories = get_gist_content()
    if not memories:
        return []

    def text_to_vec(text: str) -> Counter:
        return Counter(text.lower().split())

    def cosine(v1: Counter, v2: Counter) -> float:
        common = set(v1) & set(v2)
        num = sum(v1[x] * v2[x] for x in common)
        sum1 = sum(v ** 2 for v in v1.values())
        sum2 = sum(v ** 2 for v in v2.values())
        denom = math.sqrt(sum1) * math.sqrt(sum2)
        return num / denom if denom else 0.0

    query_vec = text_to_vec(query)
    scores = [cosine(query_vec, text_to_vec(m.get("summary", ""))) for m in memories]
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [memories[i] for i in top_indices]


# Save a new memory
@app.route("/memories", methods=["POST"])
def save_memory():
    new_memory = request.get_json()
    if not new_memory or "summary" not in new_memory:
        return jsonify({"error": "Missing memory summary."}), 400

    memories = get_gist_content()
    new_id = str(len(memories) + 1)
    new_memory["id"] = new_id
    new_memory["timestamp"] = datetime.utcnow().isoformat() + "Z"

    memories.append(new_memory)
    memories = prune_memories(memories)
    success = update_gist_content(memories)
    if success:
        # locate memory after pruning to ensure correct id
        stored_memory = next(
            (m for m in memories if m["timestamp"] == new_memory["timestamp"]),
            new_memory,
        )
        return jsonify({
            "message": "Memory saved successfully",
            "memory": stored_memory,
        }), 201
    else:
        return jsonify({"error": "Failed to update memory file."}), 500


# List all saved memories
@app.route("/memories", methods=["GET"])
def list_memories():
    return jsonify(get_gist_content())


@app.route("/memories/relevant", methods=["GET"])
def relevant_memories_endpoint():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400
    k = int(request.args.get("k", 5))
    memories = get_relevant_memories(query, k=k)
    return jsonify(memories)


# Get a specific memory by ID
@app.route("/memories/<memory_id>", methods=["GET"])
def read_memory_by_id(memory_id):
    app.logger.info("Requested memory ID: %s", memory_id)
    memories = get_gist_content()
    for memory in memories:
        if memory.get("id") == memory_id:
            return jsonify(memory)
    return jsonify({"error": "Memory not found"}), 404


# Server entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)




