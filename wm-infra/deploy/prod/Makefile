
PROVIDER = par1
ANSIBLE_SKIP :=
ANSIBLE_OPTS :=

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

modules:
	ansible-playbook -i ../../modules/main/ansible/inventory/ -l $(ANSIBLE_LIMIT) ../../modules/main/ansible/foundry-modules.yml

ingress:
	ansible-playbook -i ../../modules/main/ansible/inventory/ -l $(PROVIDER) ../../modules/main/ansible/ingress-reload.yml

playtest:
	ansible-playbook -i ../../modules/main/ansible/inventory/ -l par1 $(ANSIBLE_OPTS) ../../modules/main/ansible/playtest.yml