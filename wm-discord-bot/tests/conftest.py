from collections import namedtuple

import asyncio

import pytest


from westmarches import WestMarchesCog


@pytest.fixture()
async def westmarches(red):
    return WestMarchesCog(red, None, {})


@pytest.fixture()
def test_member(guild_factory):
    mock_member = namedtuple("Member", "id name guild display_name")
    return mock_member(323793120787693569, 'ishtanzar' , guild_factory.get(), "Testing_Name")
