from westmarches.cog import WestMarchesCog
from westmarches.commands import Commands


def test_meta(red):
    cmd = WestMarchesCog(red)
    assert cmd is not None
