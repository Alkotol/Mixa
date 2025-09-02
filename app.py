import json
import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GIST_ID = os.environ.get("GIST_ID")
GIST_FILENAME = "memories.json"  # File inside the Gist to update


def get_gist_content():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
    if response.status_code == 200:
        gist_data = response.json()
        content = gist_data["files"][GIST_FILENAME]["content"]
        return json.loads(content)
    else:
        return []


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
        return jsonify(new_memory), 201
    else:
        return jsonify({"error": "Failed to update GitHub Gist."}), 500


@app.route("/memories", methods=["GET"])
def get_memories():
    return jsonify(get_gist_content())



