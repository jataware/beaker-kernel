SHELL=/bin/bash
BASEDIR = $(shell pwd)

.PHONY:build
build:
	docker build . -t beaker-kernel:latest

.PHONY:clean
clean:
	rm -r build/ dist/

.PHONY:dev
dev:beaker_kernel/server/dev_ui/build/index.js
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

beaker_kernel/server/dev_ui/node_modules:beaker_kernel/server/dev_ui/package*.json
	export `cat .env` && \
	(cd beaker_kernel/server/dev_ui && npm install) && \
	touch beaker_kernel/server/dev_ui/node_modules

beaker_kernel/server/dev_ui/build/index.js:beaker_kernel/server/dev_ui/node_modules beaker_kernel/server/dev_ui/src/** beaker_kernel/server/dev_ui/index.css beaker_kernel/server/dev_ui/*.js beaker_kernel/server/dev_ui/*.json beaker_kernel/server/dev_ui/templates/**
	export `cat .env` && \
	(cd beaker_kernel/server/dev_ui && npm run build) && \
	touch beaker_kernel/server/dev_ui/build/*

.PHONY:changed-files
changed-files:
	find dev_ui/ \( -name "build" -prune \) -o -cnewer dev_ui/build/index.js \( -name '*.js' -or -name '*.ts' \) -ls
