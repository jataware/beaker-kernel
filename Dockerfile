FROM ghcr.io/darpa-askem/askem-julia:latest AS JULIA_BASE_IMAGE


FROM python:3.10
RUN useradd -m jupyter
EXPOSE 8888
RUN mkdir -p /usr/local/share/jupyter/kernels && chmod -R 777 /usr/local/share/jupyter/kernels

ENV JULIA_PATH=/usr/local/julia
ENV JULIA_DEPOT_PATH=/usr/local/julia
ENV JULIA_PROJECT=/home/jupyter/.julia/environments/askem

COPY --chown=1000:1000 --from=JULIA_BASE_IMAGE /usr/local/julia /usr/local/julia
COPY --chown=1000:1000 --from=JULIA_BASE_IMAGE /ASKEM-Sysimage.so /Project.toml /Manifest.toml /home/jupyter/.julia/environments/askem/
RUN chmod -R 777 /usr/local/julia/logs
RUN ln -sf /usr/local/julia/bin/julia /usr/local/bin/julia

WORKDIR /home/jupyter

# Install r-lang and kernel
RUN apt update && \
    apt install -y r-base r-cran-irkernel \
        graphviz libgraphviz-dev \
        libevent-core-2.1-7 libevent-pthreads-2.1-7 && \
    apt clean -y && \
    apt autoclean -y

WORKDIR /jupyter

# Install Python requirements
RUN pip install --upgrade --no-cache-dir hatch pip

# Install project requirements
COPY --chown=1000:1000 pyproject.toml README.md hatch_build.py /jupyter/
# Hack to install requirements without requiring the rest of the files
RUN pip install -e .

# Install Mira from `hackathon` branch
RUN git clone https://github.com/indralab/mira.git /mira && \
    pip install /mira/"[ode,tests,dkg-client,sbml]" && \
    rm -r /mira

# Kernel must be placed in a specific spot in the filesystem
# TODO: Replace this with helper that just copies the required file(s) via a python script?
COPY beaker_kernel/kernel.json /usr/local/share/jupyter/kernels/beaker_kernel/kernel.json

# Copy src code over
COPY --chown=1000:1000 . /jupyter
RUN chown -R 1000:1000 /jupyter
RUN pip install .

# Switch to non-root user. It is crucial for security reasons to not run jupyter as root user!
USER jupyter

# Install Julia kernel (as user jupyter)
RUN /usr/local/julia/bin/julia -J /home/jupyter/.julia/environments/askem/ASKEM-Sysimage.so -e 'using IJulia; IJulia.installkernel("julia"; julia=`/usr/local/julia/bin/julia -J /home/jupyter/.julia/environments/askem/ASKEM-Sysimage.so --threads=4`)'

# Service
CMD ["python", "service/main.py", "--ip", "0.0.0.0"]
