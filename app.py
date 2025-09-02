import json
import requests
from flask import Flask, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GIST_FILENAME = "mixa_memories.json"
GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def load_memories_from_gist():
    res = requests.get(GIST_API_URL, headers=HEADERS)
    res.raise_for_status()
    gist_data = res.json()
    content = gist_data["files"][GIST_FILENAME]["content"]
    return json.loads(content)

def save_memories_to_gist(memories):
    updated_content = json.dumps(memories, indent=2, ensure_ascii=False)
    payload = {
        "files": {
            GIST_FILENAME: {
                "content": updated_content
            }
        }
    }
    res = requests.patch(GIST_API_URL, headers=HEADERS, data=json.dumps(payload))
    res.raise_for_status()

@app.route('/memories', methods=['GET'])
def get_memories():
    try:
        memories = load_memories_from_gist()
        return jsonify(memories)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/memories', methods=['POST'])
def add_memory():
    data = request.get_json()
    if not data or 'summary' not in data:
        return jsonify({'error': 'Missing summary'}), 400

    try:
        memories = load_memories_from_gist()
    except:
        memories = []

    new_memory = {
        "id": str(len(memories) + 1),
        "summary": data['summary'],
        "tags": data.get("tags", []),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    memories.append(new_memory)

    try:
        save_memories_to_gist(memories)
    except Exception as e:
        return jsonify({"error": f"Failed to save memory: {str(e)}"}), 500

    return jsonify({"message": "Memory saved successfully", "memory": new_memory}), 201

@app.route('/')
def home():
    return "Mixa's Gist-powered memory server is running 💾", 200


