SHELL=/bin/bash
BASEDIR = $(shell pwd)

.PHONY:build
build:
	docker build . -t jupyter-llm:latest

.PHONY:dev
dev:dev_ui/build/index.js
	if [[ "$$(docker compose ps | grep 'jupyter')" == "" ]]; then \
		docker compose pull && \
		docker compose up -d --build && \
		(sleep 1; python -m webbrowser "http://localhost:8888/dev_ui"); \
		docker compose logs -f jupyter || true; \
	else \
		docker compose down jupyter && \
		docker compose up -d jupyter && \
		(sleep 1; python -m webbrowser "http://localhost:8888/dev_ui"); \
		docker compose logs -f jupyter || true; \
	fi


.env:
	@if [[ ! -e ./.env ]]; then \
		cp env.example .env; \
		echo "Don't forget to set your OPENAI key in the .env file!"; \
	fi

dev_ui/build/index.js:dev_ui/src/** dev_ui/index.css dev_ui/*.js dev_ui/*.json dev_ui/templates/**
	export `cat .env` && \
	(cd dev_ui && npm run build) && \
	touch dev_ui/build/*

.PHONY:dev-install
dev-install:.env
	@poetry install; \
	make dev_ui/build/index.js; \
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
	find dev_ui/ \( -name "build" -prune \) -o -cnewer dev_ui/build/index.js \( -name '*.js' -or -name '*.ts' \) -ls
