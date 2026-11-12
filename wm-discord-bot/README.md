# Discord bot

This bot is built on top of the [Red framework](https://github.com/Cog-Creators/Red-DiscordBot?tab=readme-ov-file#--------red-discord-bot--). It offers many plugins ([cogs](https://index.discord.red/)) in addition to not having to implement all the logic to have a Discord bot based on [discord.py](https://discordpy.readthedocs.io/en/stable/)

For local Docker Compose deployment, configure environment variables at the
project root. Compose maps `API_ADMIN_KEY` to the bot's `API_TOKEN` and passes
the shared `MGMNT_API_SECRET` to both the bot and the management API.

# Commands
Commands are spread in several files, according to their domain:
- forward.py
- foundry.py
- inkarnate.py
- kanka.py
- management.py
- sessions.py

## Forward module

This is inspired by the forward cog, on steroids for the campaign. There are 2 commands and 2 listeners in this module:

- `[p] gm`
  
This command is used by players to send a question to the GM team. Either via PM or in a public channel.
The question and its attachments are forwarded to a dedicated "questions" channel in the GM discord server as an embedded message including the author and the date.

- `[p] gm_setforward <channel_id>`

This command is used to configure the "questions" channel where player message will be forwarded

- `on_question_thread_message`

On a message with a single ✅ (:whitecheckmark:) emoji in a Thread in the "questions" channel, this listener will add an info message that the question has been resolved, add a ✅ reaction to the message starting the Thread (supposed to be the forwarded question) and close the Thread.

- `forward_on_message_without_command`

On a message in a Thread of either the "downtime" or "character sheets" channels, this listenener forwards it to dedicated notification channel in the GM server. The goal is for GM to see messages in any Threads without joining each Thread.

## S3 management

`[p] s3 password` provisions Object Storage credentials through the
[management API](../wm-management-api/README.md). The bot checks GM-guild
membership and the API independently verifies the current Discord username and
membership. No arguments are required; the application is identified by your
Discord ID.

The API revokes every existing key before creating a replacement, then sends
the new credentials in a private message that is deleted after 30 seconds. A
creation or delivery failure can therefore leave the previous key revoked.
Scaleway returns each secret only once; if the DM fails, the secret cannot be
retrieved and the next command replaces that key again. A success reaction is
added only after credentials have been delivered.
Keys expire automatically after four hours by default; administrators can
configure the API's `S3_EDITORS_KEY_TTL` to change their lifetime.

The API also exposes `POST /s3/credential/revoke` for later authenticated
administrative use with the same member JSON. Automatic offboarding revocation
is not wired to a bot command.

## Foundry module
All commands here are grouped in the foundry group.

Most of those commands are using the API client from the wm-utils project to send HTTP queries to the Management API.
- `[p] foundry player_add @player`

Add a player to foundry.

- `[p] foundry player_link <foundry_username> [@player]`

When a player changes its username on discord, this can be used to re-link a foundry user and a discord user.

- `[p] foundry player_set_gm [@player]`

Set a user as GM on Foundry

- `[p] foundry player_remove_gm`

Set a user as Player on Foundry

- `[p] foundry online`

List users currently connected on Foundry

- `[p] foundry restart`

Restart Foundry

- `[p] foundry backup`

Create a foundry.backup job in the Redis queue to be processed by the worker

## Inkarnate module

- `[p] inkarnate password`

Fetch the Inkarnate password from secret manager and send it in the temporary private message

- `[p] inkarnate update_password`

Fetch the Inkarnate password from secret manager, login, change the password with a new random one and update secrets manager

## Kanka module

- `[p] kanka list_users`

List all the users of the campaign

- `[p] kanka set_gm @player`

Set a user as part of the GM group of the kanka campaign and remove him from the players group

- `[p] kanka remove_gm @player`

Set a user as part of the players group of the kanka campaign and remove him from the GM group

- `[p] kanka search <query>`

Search in the kanka content indexed locally and list all the documents that matches with links
