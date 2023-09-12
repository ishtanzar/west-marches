import asyncio

import pytest


from westmarches import WestMarchesCog


@pytest.fixture()
async def westmarches(red):
    return WestMarchesCog(red, None, {})

