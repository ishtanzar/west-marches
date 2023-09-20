from westmarches import WestMarchesCog


async def test_s3_password(westmarches: WestMarchesCog, test_member):
    await westmarches.s3_passwd(test_member)

