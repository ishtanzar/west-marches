let DISCORD_BOT_SECRET = process.env.DISCORD_BOT_SECRET;

module.exports = {
    apps: [{
        name: "discordbot",
        interpreter: "/usr/bin/python3",
        // interpreter_args : "-m debugpy --listen 0.0.0.0:5679", // VScode
        // interpreter_args: "/usr/local/lib/python3.8/dist-packages/pydevd.py --multiprocess --port 5679 --client 172.17.0.1 --file", // PyCharm
        script: "/opt/project/wm-discord-workaround/src/__main__.py",
        ignore_watch: [],
        watch: "/opt/project/wm-discord-workaround/src"
    }]
}