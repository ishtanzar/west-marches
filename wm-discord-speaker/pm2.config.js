let DISCORD_BOT_SECRET = process.env.DISCORD_BOT_SECRET;
let DISCORD_OWNER_ID = process.env.DISCORD_OWNER_ID;

module.exports = {
  apps : [{
    name: "discordbot",
    interpreter: "/usr/bin/python3",
    // interpreter_args : "-m debugpy --listen 0.0.0.0:5679", // VScode
    interpreter_args : "/usr/local/lib/python3.8/dist-packages/pydevd.py --multiprocess --port 5679 --client 172.17.0.1 --file", // PyCharm
    script : "/usr/local/bin/redbot",
    args : `westmarches --mentionable --token=${DISCORD_BOT_SECRET} --prefix=YVwWFZyjiFQH --owner=${DISCORD_OWNER_ID}`,
    ignore_watch: ['data', '/opt/project/wm-discord-speaker/src/westmarches/__pycache__'],
    watch: "/opt/project/wm-discord-speaker/src"
  }]
}