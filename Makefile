SHELL=/usr/bin/env bash
BASEDIR = $(shell pwd)

.PHONY:init
init:
	make .env beaker-vue/node_modules

.PHONY:build
build:
	make beaker_kernel/server/ui/index.html
	hatch build

.PHONY:clean
clean:
	rm -r build/* dist/* beaker_kernel/server/ui/*

.PHONY:docs-up
docs-up:
	(cd docs && docker compose up -d) && \
	(sleep 1; python -m webbrowser "http://localhost:4000/")

.PHONY:docs-down
docs-down:
	(cd docs && docker compose down)

.PHONY:dev
dev:
	docker compose up -d --build && \
	(sleep 1; python -m webbrowser "http://localhost:8888/"); \
	docker compose logs -f jupyter || true; \

.env:
	@if [[ ! -e ./.env ]]; then \
		cp env.example .env; \
		echo "Don't forget to set your OPENAI key in the .env file!"; \
	fi

beaker-vue/node_modules:beaker-vue/package*.json
	export `cat .env` && \
	(cd beaker-vue && npm install) && \
	touch beaker-vue/node_modules

beaker_kernel/server/ui/index.html:beaker-vue/node_modules beaker-vue/**
	rm -r beaker_kernel/server/ui/* ; \
	(cd beaker-vue/ && npm run build) && \
	cp -r beaker-vue/dist/* beaker_kernel/server/ui/

.PHONY:changed-files
changed-files:
	find dev_ui/ \( -name "build" -prune \) -o -cnewer dev_ui/build/index.js \( -name '*.js' -or -name '*.ts' \) -ls
