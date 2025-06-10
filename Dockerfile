FROM python:3.10
RUN useradd -m jupyter
RUN useradd -m user
EXPOSE 8888

RUN apt update && apt install -y lsof

# Install Python requirements
RUN pip install --upgrade --no-cache-dir hatch pip

# Install project requirements
# Hack to install requirements without requiring the rest of the files
COPY --chown=1000:1000 pyproject.toml /jupyter/
RUN bash -c "pip install --no-build-isolation --no-cache-dir -r <(\
            echo 'import tomli; \
            c = tomli.load(open(\"/jupyter/pyproject.toml\", \"rb\")); \
            d = c[\"project\"][\"dependencies\"]; \
            print(\"\n\".join(f\"{dep}\" for dep in d))' | python \
        )"

# Copy src code over
COPY --chown=1000:1000 . /jupyter
RUN chown -R 1000:1000 /jupyter
RUN pip install --no-build-isolation --no-cache-dir /jupyter

RUN mkdir -m 755 /var/run/beaker
RUN mkdir -m 777 /var/run/beaker/checkpoints

# Set default server env variables
ENV BEAKER_AGENT_USER=jupyter
ENV BEAKER_SUBKERNEL_USER=user
ENV BEAKER_RUN_PATH=/var/run/beaker

VOLUME /var/run/beaker /jupyter /jupyter/beaker_kernel/service/ui /usr/local/share/jupyter/kernels/beaker_kernel

# Beaker Server should run as root, but local notebooks should not as Beaker Server sets the UID of running kernels to
# an unprivileged user account when kernel processes are spawned
USER root

# Simple "notebook" service
CMD ["python3.10", "-m", "beaker_kernel.service.server", "--ip", "0.0.0.0"]
