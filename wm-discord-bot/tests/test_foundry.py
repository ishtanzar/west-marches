from westmarches import WestMarchesCog

async def test_player_set_gm(westmarches: WestMarchesCog, ctx, test_member):
    await westmarches.update_role(ctx, test_member, 4)
