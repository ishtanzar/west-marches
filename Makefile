.PHONY: docker/foundry docker/foundry/push

docker/foundry:
	direnv exec wm-infra/deploy/prod $(MAKE) -C wm-infra/deploy/prod docker/foundry

docker/foundry/push:
	direnv exec wm-infra/deploy/prod $(MAKE) -C wm-infra/deploy/prod docker/foundry/push