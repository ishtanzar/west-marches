.PHONY: docker/foundry docker/foundry/push deploy/test deploy/test/init deploy/test/plan \
	compose/up compose/down compose/build compose/restart compose/logs compose/ps logs/discordbot

SERVICES ?=

docker/foundry:
	direnv exec wm-infra/deploy/prod $(MAKE) -C wm-infra/deploy/prod docker/foundry

docker/foundry/push:
	direnv exec wm-infra/deploy/prod $(MAKE) -C wm-infra/deploy/prod docker/foundry/push

deploy/test:
	direnv exec wm-infra/deploy/test $(MAKE) -C wm-infra/deploy/test deploy

deploy/prod:
	direnv exec wm-infra/deploy/prod $(MAKE) -C wm-infra/deploy/prod deploy

compose/up:
	docker compose up -d $(SERVICES)

compose/down:
	docker compose down

compose/build:
	docker compose build $(SERVICES)

compose/logs:
	docker compose logs -f $(SERVICES)

logs/discordbot:
	$(MAKE) -C wm-infra/deploy/prod logs/discordbot