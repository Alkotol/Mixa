import os
import sys
import pytest

# Ensure project root is on path and env vars exist before importing app
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)
os.environ.setdefault('GITHUB_TOKEN', 'test-token')
os.environ.setdefault('GIST_ID', 'test-gist')

import app  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    test_memories = []

    def fake_get_gist_content(force_refresh=False):
        return test_memories

    def fake_update_gist_content(memories):
        nonlocal test_memories
        test_memories = memories
        return True

    monkeypatch.setattr(app, 'get_gist_content', fake_get_gist_content)
    monkeypatch.setattr(app, 'update_gist_content', fake_update_gist_content)
    return app.app.test_client()


def test_post_memory(client):
    resp = client.post('/memories', json={'summary': 'hello world'})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['memory']['summary'] == 'hello world'


def test_get_memories(client):
    client.post('/memories', json={'summary': 'first'})
    resp = client.get('/memories')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_get_memory_by_id(client):
    client.post('/memories', json={'summary': 'unique'})
    resp = client.get('/memories/1')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['summary'] == 'unique'
    missing = client.get('/memories/999')
    assert missing.status_code == 404


def test_relevant_memories(client):
    client.post('/memories', json={'summary': 'apple banana'})
    client.post('/memories', json={'summary': 'cat dog'})
    resp = client.get('/memories/relevant?q=apple')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) >= 1
