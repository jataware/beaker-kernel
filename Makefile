SHELL=/bin/bash
BASEDIR = $(shell pwd)

.PHONY:build
build:
	docker build . -t beaker-kernel:latest

.PHONY:dev
dev:service/dev_ui/build/index.js test.ipynb
	if [[ "$$(docker compose ps | grep 'jupyter')" == "" ]]; then \
		docker compose pull; \
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

service/dev_ui/node_modules:service/dev_ui/package*.json
	export `cat .env` && \
	(cd service/dev_ui && npm install) && \
	touch service/dev_ui/node_modules

service/dev_ui/build/index.js:service/dev_ui/node_modules service/dev_ui/src/** service/dev_ui/index.css service/dev_ui/*.js service/dev_ui/*.json service/dev_ui/templates/**
	export `cat .env` && \
	(cd service/dev_ui && npm run build) && \
	touch service/dev_ui/build/*

test.ipynb:
	if [[ ! -e "test.ipynb" ]]; then \
		cp service/dev_ui/test.ipynb test.ipynb; \
	fi


.PHONY:dev-install
dev-install:.env test.ipynb
	@poetry install; \
	make service/dev_ui/build/index.js; \
	ENVDIR=$$(poetry -q run python -c 'import os; print(os.environ.get("VIRTUAL_ENV", ""))'); \
	KERNEL_INSTALL_PATH=$${ENVDIR}/share/jupyter/kernels/beaker; \
	if [[ ! -e "$${KERNEL_INSTALL_PATH}" && -n "$${ENVDIR}" ]]; then \
		ln -s "${BASEDIR}/beaker_kernel" "$${KERNEL_INSTALL_PATH}"; \
	fi; \

.PHONY:changed-files
changed-files:
	find dev_ui/ \( -name "build" -prune \) -o -cnewer dev_ui/build/index.js \( -name '*.js' -or -name '*.ts' \) -ls
