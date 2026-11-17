
PROVIDER = fr-par-1
ANSIBLE_SKIP :=
ANSIBLE_OPTS :=
FOUNDRY_IMAGE ?= rg.fr-par.scw.cloud/westmarches-prod/wm-docker-foundry:latest
REFRESH ?= false
APT_REFRESH = $(if $(filter true,$(REFRESH)),$(shell \date -u +%s%N),initial)
KUBE_CONFIG ?= $(CURDIR)/kubeconfig.yml
KUBECTL = KUBECONFIG="$(KUBE_CONFIG)" kubectl

.PHONY: logs/discordbot

ifdef SKIP_MODULES
ANSIBLE_SKIP := $(ANSIBLE_SKIP),modules
endif

ifdef SKIP_FOUNDRY
ANSIBLE_SKIP := $(ANSIBLE_SKIP),foundry
endif

ifdef SKIP_CERT
ANSIBLE_SKIP := $(ANSIBLE_SKIP),cert
endif

ifdef ONLY_BACKUP
ANSIBLE_OPTS := $(ANSIBLE_OPTS) --tags backup
else ifdef ANSIBLE_SKIP
ANSIBLE_OPTS := $(ANSIBLE_OPTS) --skip-tags $(ANSIBLE_SKIP)
endif

export ANSIBLE_DISPLAY_SKIPPED_HOSTS = false

deploy:
	terraform15 apply

init:
	terraform15 init -upgrade

modules:
	ansible-playbook -i ../../modules/main/ansible/inventory/ -l $(PROVIDER) ../../modules/main/ansible/foundry-modules.yml

ingress:
	ansible-playbook -i ../../modules/main/ansible/inventory/ -l $(PROVIDER) ../../modules/main/ansible/ingress-reload.yml

playtest:
	ansible-playbook -i ../../modules/main/ansible/inventory/ -l $(PROVIDER) $(ANSIBLE_OPTS) ../../modules/main/ansible/playtest.yml

test:
	ansible-playbook -i ../../modules/main/ansible/inventory/ -l $(PROVIDER) $(ANSIBLE_OPTS) ../../modules/main/ansible/test.yml

docker/foundry:
	docker build \
		--file ../../docker/foundry/Dockerfile \
		--tag "$(FOUNDRY_IMAGE)" \
		--build-arg APT_REFRESH="$(APT_REFRESH)" \
		--secret id=aws_access_key_id,env=FOUNDRY_BUCKET_ACCESS_KEY_ID \
		--secret id=aws_secret_access_key,env=FOUNDRY_BUCKET_SECRET_ACCESS_KEY \
		../..

docker/foundry/push:
	docker push "$(FOUNDRY_IMAGE)"

exec/foundry:
	$(KUBECTL) exec -it -n lesaventuriersducairn-prod deploy/foundry -c foundry -- /bin/bash

logs/foundry:
	$(KUBECTL) logs -f -n lesaventuriersducairn-prod deploy/foundry -c foundry

logs/discordbot:
	$(KUBECTL) logs -f --tail=200 -n lesaventuriersducairn-prod deploy/discordbot -c discordbot
