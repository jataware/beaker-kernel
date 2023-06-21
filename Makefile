SHELL=/bin/bash
BASEDIR = $(shell pwd)

.PHONY:build
build:
	docker build . -t jupyter-llm:latest

.PHONY:dev
dev:
	export `cat .env` && (cd dev_ui/ && npm run build) && poetry run python dev.py

.PHONY:dev-install
dev-install:
	poetry install; \
	(cd dev_ui && npm install); \
	ENVDIR=$$(poetry -q run python -c 'import os; print(os.environ.get("VIRTUAL_ENV", ""))'); \
	KERNEL_INSTALL_PATH=$${ENVDIR}/share/jupyter/kernels/llmkernel; \
	if [[ ! -e "$${KERNEL_INSTALL_PATH}" && -n "$${ENVDIR}" ]]; then \
		ln -s "${BASEDIR}/llmkernel" "$${KERNEL_INSTALL_PATH}"; \
	fi; \
	if [[ ! -e "./test.ipynb" ]]; then \
		cp dev_ui/test.ipynb ./test.ipynb; \
	fi
