SHELL=/bin/bash
BASEDIR = $(shell pwd)

.PHONY:build
build:
	docker build . -t jupyter-llm:latest

.PHONY:dev
dev:
	export `cat .env` && (cd dev_ui/ && npm run build) && poetry run python dev.py

.env:
	@if [[ ! -e ./.env ]]; then \
		cp env.example .env; \
		echo "Don't forget to set your OPENAI key in the .env file!"; \
	fi

.PHONY:dev-install
dev-install:.env
	@poetry install; \
	(cd dev_ui && npm install); \
	ENVDIR=$$(poetry -q run python -c 'import os; print(os.environ.get("VIRTUAL_ENV", ""))'); \
	KERNEL_INSTALL_PATH=$${ENVDIR}/share/jupyter/kernels/llmkernel; \
	if [[ ! -e "$${KERNEL_INSTALL_PATH}" && -n "$${ENVDIR}" ]]; then \
		ln -s "${BASEDIR}/llmkernel" "$${KERNEL_INSTALL_PATH}"; \
	fi; \
	if [[ ! -e "./test.ipynb" ]]; then \
		cp dev_ui/test.ipynb ./test.ipynb; \
	fi

.PHONY:changed-files
changed-files:
	find dev_ui/ -not -path build -cnewer dev_ui/build/index.js
