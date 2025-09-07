import json
import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GIST_ID = os.environ.get("GIST_ID")
GIST_FILENAME = "mixa_memories.json"


# Load memory list from GitHub Gist
def get_gist_content():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/gists/{GIST_ID}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        gist_data = response.json()
        files = gist_data.get("files", {})
        if GIST_FILENAME in files:
            file_content = files[GIST_FILENAME]["content"]
            try:
                return json.loads(file_content)
            except json.JSONDecodeError:
                return []
    return []


# Update the Gist with new memory list
def update_gist_content(memories):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
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
        data=json.dumps(data)
    )
    return response.status_code == 200


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
    success = update_gist_content(memories)
    if success:
        return jsonify({
            "message": "Memory saved successfully",
            "memory": new_memory
        }), 201
    else:
        return jsonify({"error": "Failed to update memory file."}), 500


# List all saved memories
@app.route("/memories", methods=["GET"])
def list_memories():
    return jsonify(get_gist_content())


# Get a specific memory by ID
@app.route("/memories/<memory_id>", methods=["GET"])
def read_memory_by_id(memory_id):
    print(f"Requested memory ID: {memory_id}")  # <-- Add this:
    memories = get_gist_content()
    for memory in memories:
        if memory.get("id") == memory_id:
            return jsonify(memory)
    return jsonify({"error": "Memory not found"}), 404


# Server entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)




