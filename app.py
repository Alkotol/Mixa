from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from OpenAI

MEMORY_FILE = "mixa_memories.json"

def load_memories():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memories(memories):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memories, f, indent=2, ensure_ascii=False)

@app.route("/memories", methods=["POST"])
def save_memory():
    data = request.get_json()
    if not data or "summary" not in data:
        return jsonify({"error": "Missing memory summary"}), 400

    memories = load_memories()
    new_memory = {
        "id": f"mem-{len(memories)+1:03d}",
        "summary": data["summary"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tags": data.get("tags", [])
    }
    memories.append(new_memory)
    save_memories(memories)
    return jsonify({"message": "Memory saved", "memory": new_memory}), 201

@app.route("/memories", methods=["GET"])
def get_memories():
    return jsonify(load_memories()), 200

if __name__ == "__main__":
    app.run(debug=True)
