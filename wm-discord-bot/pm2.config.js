let DISCORD_BOT_SECRET = process.env.DISCORD_BOT_SECRET;
let DISCORD_OWNER_ID = process.env.DISCORD_OWNER_ID;

module.exports = {
    apps: [{
        name: "discordbot",
        interpreter: "/opt/venv/bin/python",
        // interpreter_args : "-m debugpy --listen 0.0.0.0:5679", // VScode
        // interpreter_args: "/opt/venv/lib/python3.9/site-packages/pydevd.py --multiprocess --port 5679 --client 172.17.0.1 --file", // PyCharm
        script: "/opt/venv/bin/redbot",
        args: [
            'westmarches',
            '--mentionable',
            `--token=${DISCORD_BOT_SECRET}`,
            '--prefix=YVwWFZyjiFQH',
            '--load-cogs=westmarches',
            `--owner=${DISCORD_OWNER_ID}`,
            // '--intents=2097151'
        ],
        ignore_watch: [
            'data',
            '/opt/project/wm-discord-bot/src/westmarches/__pycache__',
            '/opt/project/wm-discord-bot/src/westmarches/commands/__pycache__'
        ],
        watch: "/opt/project/wm-discord-bot/src"
    }]
}