.DEFAULT_GOAL := help

.PHONY: help
help: ## help on rule's targets
	@awk --posix 'BEGIN {FS = ":.*?## "} /^[[:alpha:][:space:]_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)


.env: .env-devel ## creates .env file from defaults in .env-devel
	$(if $(wildcard $@), \
	@echo "WARNING #####  $< is newer than $@ ####"; diff -uN $@ $<; false;,\
	@echo "WARNING ##### $@ does not exist, cloning $< as $@ ############"; cp $< $@)


.PHONY: install-ci
install-ci: ## installs osparc client and dependencies
	pip install git+https://github.com/ITISFoundation/osparc-simcore-python-client.git
	pip install python-dotenv jupytext


objects = $(wildcard *.py)
outputs := $(objects:.py=.ipynb)

%.ipynb: %.py
	jupytext --to notebook $<

.PHONY: notebooks
notebooks: $(outputs) ## convert all py scripts inot notebook


.PHONY: clean
_GIT_CLEAN_ARGS = -dxf -e .vscode -e TODO.md
clean: ## cleans all unversioned files in project and temp files create by this makefile
	# Cleaning unversioned
	@git clean -n $(_GIT_CLEAN_ARGS)
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	@echo -n "$(shell whoami), are you REALLY sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	@git clean $(_GIT_CLEAN_ARGS)
