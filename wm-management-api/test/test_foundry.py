import pytest

@pytest.mark.disable_auth_mock
async def test_foundry_auth(client):
    assert (await client.post('/foundry/restart')).status_code == 401
    assert (await client.open('/foundry/users', method='search')).status_code == 401
    assert (await client.post('/foundry/users', json={'role': 4})).status_code == 401
    assert (await client.put('/foundry/users/123_456', json={'role': 4})).status_code == 401

async def test_foundry_set_gm(client):
    response = await client.put('/foundry/users/123_456', json={'role': 4})
    assert response.status_code == 200