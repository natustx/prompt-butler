import pytest
from fastapi.testclient import TestClient

from prompt_butler.main import app
from prompt_butler.models import Prompt


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with isolated storage."""
    from prompt_butler.services.storage import PromptStorage

    test_storage = PromptStorage(prompts_dir=tmp_path)

    import prompt_butler.routers.prompts as prompts_router

    monkeypatch.setattr(prompts_router, '_storage', test_storage)

    return TestClient(app), test_storage


class TestListPrompts:
    def test_list_prompts_empty(self, client):
        test_client, _storage = client

        response = test_client.get('/api/prompts/')

        assert response.status_code == 200
        assert response.json() == []

    def test_list_prompts_returns_items(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content 1', tags=['one']))

        response = test_client.get('/api/prompts/')

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == 'prompt1'
        assert data[0]['tags'] == ['one']


class TestGetPrompt:
    def test_get_prompt_success(self, client):
        test_client, storage = client
        storage.create(Prompt(name='prompt1', system_prompt='Content 1'))

        response = test_client.get('/api/prompts/prompt1')

        assert response.status_code == 200
        assert response.json()['name'] == 'prompt1'

    def test_get_prompt_not_found(self, client):
        test_client, _storage = client

        response = test_client.get('/api/prompts/missing')

        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()


class TestCreatePrompt:
    def test_create_prompt_success(self, client):
        test_client, _storage = client

        payload = {
            'name': 'prompt1',
            'description': 'Test description',
            'system_prompt': 'System content',
            'user_prompt': 'User content',
            'group': 'testing',
            'tags': ['tag1', 'tag2'],
        }

        response = test_client.post('/api/prompts/', json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'prompt1'
        assert data['group'] == 'testing'
        assert data['tags'] == ['tag1', 'tag2']

    def test_create_prompt_conflict(self, client):
        test_client, storage = client
        storage.create(Prompt(name='prompt1', system_prompt='Content 1'))

        response = test_client.post('/api/prompts/', json={
            'name': 'prompt1',
            'system_prompt': 'Another content',
        })

        assert response.status_code == 409
        assert 'already exists' in response.json()['detail']


class TestUpdatePrompt:
    def test_update_prompt_success(self, client):
        test_client, storage = client
        storage.create(Prompt(name='prompt1', system_prompt='Content 1'))

        response = test_client.put('/api/prompts/prompt1', json={
            'description': 'Updated',
            'group': 'updated-group',
            'tags': ['tag1'],
        })

        assert response.status_code == 200
        data = response.json()
        assert data['description'] == 'Updated'
        assert data['group'] == 'updated-group'
        assert data['tags'] == ['tag1']
        updated = storage.read('prompt1', group='updated-group')
        assert updated is not None
        assert updated.description == 'Updated'
        assert updated.group == 'updated-group'
        assert updated.tags == ['tag1']

    def test_update_prompt_not_found(self, client):
        test_client, _storage = client

        response = test_client.put('/api/prompts/missing', json={'description': 'Updated'})

        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()

    def test_update_prompt_invalid_group(self, client):
        test_client, storage = client
        storage.create(Prompt(name='prompt1', system_prompt='Content 1'))

        response = test_client.put('/api/prompts/prompt1', json={'group': 'invalid group!'})

        assert response.status_code == 422


class TestDeletePrompt:
    def test_delete_prompt_success(self, client):
        test_client, storage = client
        storage.create(Prompt(name='prompt1', system_prompt='Content 1'))

        response = test_client.delete('/api/prompts/prompt1')

        assert response.status_code == 204

    def test_delete_prompt_not_found(self, client):
        test_client, _storage = client

        response = test_client.delete('/api/prompts/missing')

        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()


class TestPromptValidation:
    def test_create_prompt_missing_system_prompt(self, client):
        test_client, _storage = client

        response = test_client.post('/api/prompts/', json={'name': 'prompt1'})

        assert response.status_code == 422

    def test_create_prompt_invalid_tag(self, client):
        test_client, _storage = client

        response = test_client.post('/api/prompts/', json={
            'name': 'prompt1',
            'system_prompt': 'System content',
            'tags': ['bad tag!'],
        })

        assert response.status_code == 422
