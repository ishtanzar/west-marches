import pytest
from collections import namedtuple

from westmarches import WestMarchesCog


@pytest.fixture()
def test_member(guild_factory):
    mock_member = namedtuple("Member", "id guild display_name")
    return mock_member(323793120787693569, guild_factory.get(), "Testing_Name")


async def test_player_set_gm(westmarches: WestMarchesCog, ctx, test_member):
    await westmarches.update_role(ctx, test_member, 4)
