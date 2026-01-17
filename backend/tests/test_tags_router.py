import pytest
from fastapi.testclient import TestClient

from prompt_butler.main import app
from prompt_butler.models import Prompt


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with isolated storage."""
    from prompt_butler.services.storage import PromptStorage

    test_storage = PromptStorage(prompts_dir=tmp_path)

    import prompt_butler.routers.tags as tags_router

    monkeypatch.setattr(tags_router, '_storage', test_storage)

    return TestClient(app), test_storage


class TestListTags:
    def test_list_tags_empty(self, client):
        test_client, storage = client

        response = test_client.get('/api/tags/')

        assert response.status_code == 200
        assert response.json() == []

    def test_list_tags_returns_tag_counts(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', tags=['coding', 'python']))
        storage.create(Prompt(name='prompt2', system_prompt='Content', tags=['coding']))
        storage.create(Prompt(name='prompt3', system_prompt='Content', tags=['writing']))

        response = test_client.get('/api/tags/')

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3

        tag_dict = {item['tag']: item['count'] for item in data}
        assert tag_dict['coding'] == 2
        assert tag_dict['python'] == 1
        assert tag_dict['writing'] == 1

    def test_list_tags_sorted_alphabetically(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', tags=['zebra', 'apple']))

        response = test_client.get('/api/tags/')

        assert response.status_code == 200
        data = response.json()

        tags = [item['tag'] for item in data]
        assert tags == ['apple', 'zebra']

    def test_list_tags_response_format(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', tags=['test-tag']))

        response = test_client.get('/api/tags/')

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert 'tag' in data[0]
        assert 'count' in data[0]
        assert data[0]['tag'] == 'test-tag'
        assert data[0]['count'] == 1


class TestRenameTag:
    def test_rename_tag_success(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', tags=['old-tag', 'other']))
        storage.create(Prompt(name='prompt2', system_prompt='Content', tags=['old-tag']))

        response = test_client.post('/api/tags/rename', json={'old_tag': 'old-tag', 'new_tag': 'new-tag'})

        assert response.status_code == 200
        data = response.json()
        assert data['updated_count'] == 2

        prompt1 = storage.read('prompt1')
        prompt2 = storage.read('prompt2')
        assert 'new-tag' in prompt1.tags
        assert 'old-tag' not in prompt1.tags
        assert 'other' in prompt1.tags
        assert 'new-tag' in prompt2.tags
        assert 'old-tag' not in prompt2.tags

    def test_rename_tag_not_found(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', tags=['some-tag']))

        response = test_client.post('/api/tags/rename', json={'old_tag': 'nonexistent', 'new_tag': 'new-tag'})

        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()

    def test_rename_tag_invalid_new_tag(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', tags=['old-tag']))

        response = test_client.post('/api/tags/rename', json={'old_tag': 'old-tag', 'new_tag': 'invalid tag!'})

        assert response.status_code == 422

    def test_rename_tag_response_format(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', tags=['old-tag']))

        response = test_client.post('/api/tags/rename', json={'old_tag': 'old-tag', 'new_tag': 'new-tag'})

        assert response.status_code == 200
        data = response.json()
        assert 'updated_count' in data
        assert isinstance(data['updated_count'], int)
