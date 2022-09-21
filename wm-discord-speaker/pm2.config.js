let DISCORD_BOT_SECRET = process.env.DISCORD_BOT_SECRET;
let DISCORD_OWNER_ID = process.env.DISCORD_OWNER_ID;

module.exports = {
  apps : [{
    name: "discordbot",
    interpreter: "/usr/bin/python3",
    interpreter_args : "-m debugpy --listen 0.0.0.0:5679",
    script : "/usr/local/bin/redbot",
    args : `westmarches --mentionable --token=${DISCORD_BOT_SECRET} --prefix=YVwWFZyjiFQH --owner=${DISCORD_OWNER_ID}`,
    ignore_watch: ["data"],
    watch: "/opt/project/wm-discord-speaker/src"
  }]
}