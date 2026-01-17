import pytest
from fastapi.testclient import TestClient

from prompt_butler.main import app
from prompt_butler.models import Prompt


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with isolated storage."""
    from prompt_butler.services.storage import PromptStorage

    test_storage = PromptStorage(prompts_dir=tmp_path)

    import prompt_butler.routers.groups as groups_router

    monkeypatch.setattr(groups_router, '_storage', test_storage)

    return TestClient(app), test_storage


class TestListGroups:
    def test_list_groups_empty(self, client):
        test_client, storage = client

        response = test_client.get('/api/groups/')

        assert response.status_code == 200
        assert response.json() == []

    def test_list_groups_returns_group_counts(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', group='coding'))
        storage.create(Prompt(name='prompt2', system_prompt='Content', group='coding'))
        storage.create(Prompt(name='prompt3', system_prompt='Content', group='writing'))
        storage.create(Prompt(name='prompt4', system_prompt='Content', group=''))

        response = test_client.get('/api/groups/')

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3

        group_dict = {item['group']: item['count'] for item in data}
        assert group_dict['coding'] == 2
        assert group_dict['writing'] == 1
        assert group_dict[''] == 1

    def test_list_groups_sorted_alphabetically(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', group='zebra'))
        storage.create(Prompt(name='prompt2', system_prompt='Content', group='apple'))

        response = test_client.get('/api/groups/')

        assert response.status_code == 200
        data = response.json()

        groups = [item['group'] for item in data]
        assert groups == ['apple', 'zebra']

    def test_list_groups_response_format(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', group='test-group'))

        response = test_client.get('/api/groups/')

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert 'group' in data[0]
        assert 'count' in data[0]
        assert data[0]['group'] == 'test-group'
        assert data[0]['count'] == 1

    def test_list_groups_includes_ungrouped(self, client):
        test_client, storage = client

        storage.create(Prompt(name='ungrouped', system_prompt='Content', group=''))

        response = test_client.get('/api/groups/')

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]['group'] == ''
        assert data[0]['count'] == 1


class TestRenameGroup:
    def test_rename_group_success(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content 1', group='old-group'))
        storage.create(Prompt(name='prompt2', system_prompt='Content 2', group='old-group'))

        response = test_client.post('/api/groups/rename', json={
            'old_group': 'old-group',
            'new_group': 'new-group',
        })

        assert response.status_code == 200
        data = response.json()
        assert data['updated_count'] == 2

        # Verify folder was renamed
        assert not (storage.prompts_dir / 'old-group').exists()
        assert (storage.prompts_dir / 'new-group').exists()

    def test_rename_group_not_found(self, client):
        test_client, storage = client

        response = test_client.post('/api/groups/rename', json={
            'old_group': 'nonexistent',
            'new_group': 'new-group',
        })

        assert response.status_code == 404
        assert 'not found' in response.json()['detail']

    def test_rename_group_target_exists(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', group='group-a'))
        storage.create(Prompt(name='prompt2', system_prompt='Content', group='group-b'))

        response = test_client.post('/api/groups/rename', json={
            'old_group': 'group-a',
            'new_group': 'group-b',
        })

        assert response.status_code == 409
        assert 'already exists' in response.json()['detail']

    def test_rename_group_invalid_new_name(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', group='old-group'))

        response = test_client.post('/api/groups/rename', json={
            'old_group': 'old-group',
            'new_group': 'invalid name!',
        })

        assert response.status_code == 422  # Validation error

    def test_rename_group_empty_group(self, client):
        test_client, storage = client

        response = test_client.post('/api/groups/rename', json={
            'old_group': '',
            'new_group': 'new-group',
        })

        assert response.status_code == 422  # Validation error - min_length=1

    def test_rename_group_response_format(self, client):
        test_client, storage = client

        storage.create(Prompt(name='prompt1', system_prompt='Content', group='test-group'))

        response = test_client.post('/api/groups/rename', json={
            'old_group': 'test-group',
            'new_group': 'renamed-group',
        })

        assert response.status_code == 200
        data = response.json()
        assert 'updated_count' in data
        assert isinstance(data['updated_count'], int)
