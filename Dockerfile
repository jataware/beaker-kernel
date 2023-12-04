ARG JULIA_IMAGE=askem-julia-base
FROM ${JULIA_IMAGE} AS JULIA_BASE_IMAGE


FROM python:3.10
RUN useradd -m jupyter
EXPOSE 8888
RUN mkdir -p /usr/local/share/jupyter/kernels && chmod -R 777 /usr/local/share/jupyter/kernels

ENV JULIA_PATH=/usr/local/julia
ENV JULIA_DEPOT_PATH=/usr/local/julia
ENV JULIA_PROJECT=/home/jupyter/.julia/environments/v1.9

COPY --from=JULIA_BASE_IMAGE /usr/local/julia /usr/local/julia
COPY --from=JULIA_BASE_IMAGE /ASKEM-Sysimage.so /usr/local/julia/lib/ASKEM-Sysimage.so
RUN chmod -R 777 /usr/local/julia/logs
RUN ln -sf /usr/local/julia/bin/julia /usr/local/bin/julia

COPY --chown=1000:1000 environments/julia /home/jupyter/.julia/environments/v1.9

WORKDIR /home/jupyter

# Install r-lang and kernel
RUN apt update && \
    apt install -y r-base r-cran-irkernel && \
    apt clean -y

WORKDIR /jupyter

# Install Python requirements
RUN pip install --no-cache-dir jupyterlab jupyterlab_server pandas matplotlib xarray numpy poetry scipy

# Install project requirements
COPY --chown=1000:1000 pyproject.toml poetry.lock /jupyter/
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-cache

# Install Mira from `hackathon` branch
RUN git clone https://github.com/indralab/mira.git /mira
WORKDIR /mira

RUN python -m pip install -e .
RUN apt update && \
    apt install -y graphviz libgraphviz-dev && \
    apt clean -y
RUN python -m pip install -e ."[ode,tests,dkg-client,sbml]"
WORKDIR /jupyter

# Kernel must be placed in a specific spot in the filesystem
COPY beaker_kernel /usr/local/share/jupyter/kernels/beaker_kernel

# Copy src code over
RUN chown 1000:1000 /jupyter
COPY --chown=1000:1000 . /jupyter

# Switch to non-root user. It is crucial for security reasons to not run jupyter as root user!
USER jupyter

# Install Julia kernel
RUN /usr/local/julia/bin/julia -J /usr/local/julia/lib/ASKEM-Sysimage.so -e 'using IJulia; IJulia.installkernel("julia"; julia=`/usr/local/julia/bin/julia -J /usr/local/julia/lib/ASKEM-Sysimage.so --threads=4`)'

# Service
CMD ["python", "service/main.py", "--ip", "0.0.0.0"]
