# Mixa Memory Service

This Flask application exposes endpoints for storing and retrieving conversational memories using a GitHub Gist as persistence.

## Environment Variables

The app requires the following environment variables:

- `GITHUB_TOKEN` – Personal access token with permissions to read and update the Gist.
- `GIST_ID` – Identifier of the Gist containing the `mixa_memories.json` file.

The service will raise an error at startup if these variables are missing.

## Features

- In-memory caching of the Gist content with a 60 second TTL.
- Automatic pruning of old memories when more than 100 are stored. Older entries are summarized.
- Embedding-based retrieval endpoint `/memories/relevant?q=<query>` returning the top related memories.
- Structured logging using Python's logging module.

## Running Tests

Install dependencies and run tests with:

```bash
pip install -r requirements.txt
pytest
```
