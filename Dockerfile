FROM python:3.10
RUN useradd -m jupyter
EXPOSE 8888

RUN apt update && apt install -y lsof

# Install Python requirements
RUN pip install --upgrade --no-cache-dir hatch pip

# Install project requirements
# Hack to install requirements without requiring the rest of the files
COPY --chown=1000:1000 pyproject.toml /jupyter/
RUN bash -c "pip install --no-build-isolation --no-cache-dir -r <(echo 'import tomli; c = tomli.load(open(\"/jupyter/pyproject.toml\", \"rb\")); d = c[\"project\"][\"dependencies\"]; print(\"\n\".join(f\"{dep}\" for dep in d))' | python)"

# Copy src code over
COPY --chown=1000:1000 . /jupyter
RUN chown -R 1000:1000 /jupyter
RUN pip install --no-build-isolation --no-cache-dir /jupyter

# Switch to non-root user. It is crucial for security reasons to not run jupyter as root user!
USER jupyter
WORKDIR /jupyter

# Simple "notebook" service
CMD ["beaker", "notebook", "--ip", "0.0.0.0"]
