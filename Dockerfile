FROM python:3.10
RUN useradd -m jupyter
EXPOSE 8888

# Install Python requirements
RUN pip install --upgrade --no-cache-dir hatch pip

# Install project requirements
COPY --chown=1000:1000 pyproject.toml README.md hatch_build.py /jupyter/

# Hack to install requirements without requiring the rest of the files
RUN pip install -e /jupyter/

# Copy src code over
COPY --chown=1000:1000 . /jupyter
RUN chown -R 1000:1000 /jupyter
RUN pip install /jupyter

# Switch to non-root user. It is crucial for security reasons to not run jupyter as root user!
USER jupyter
WORKDIR /jupyter

# Service
CMD ["python", "-m", "beaker_kernel.server.main", "--ip", "0.0.0.0"]
