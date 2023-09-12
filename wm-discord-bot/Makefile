

pytest:
	docker compose up -d --no-deps discordbot
ifdef DEBUG
		docker compose exec discordbot python /opt/venv/lib/python3.9/site-packages/pydevd.py --multiprocess --port 5679 --client 172.17.0.1 --file /opt/venv/bin/pytest /opt/project/wm-discord-bot
else
		docker compose exec discordbot python -m pytest /opt/project/wm-discord-bot
endif
