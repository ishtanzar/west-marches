import pytest

from westmarches import WestMarchesCog
from redbot.core import commands


@pytest.fixture()
async def wm_cog(red):
    return WestMarchesCog(red)


def test_train(wm_cog: WestMarchesCog):
    data = wm_cog._load_intents()
    wm_cog._train(data)


def test_chat(wm_cog: WestMarchesCog):
    response = wm_cog._predict('hein, que tu comprends rien ?')

    assert response == 'insult'
