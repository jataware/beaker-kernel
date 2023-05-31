FROM python:3.10
RUN useradd -m jupyter
EXPOSE 8888
WORKDIR /jupyter

# Install Julia
RUN wget https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.0-linux-x86_64.tar.gz
RUN tar -xzf julia-1.9.0-linux-x86_64.tar.gz && mv julia-1.9.0 /opt/julia && \
    ln -s /opt/julia/bin/julia /usr/local/bin/julia && rm julia-1.9.0-linux-x86_64.tar.gz

# Add Julia to Jupyter
USER 1000
RUN julia -e 'using Pkg; Pkg.add("IJulia");'

# Install Julia requirements
RUN julia -e ' \
    packages = [ \
        "Catlab", "AlgebraicPetri", "DataSets", "EasyModelAnalysis", "XLSX", "Plots", "Downloads", \
        "DataFrames", "ModelingToolkit", "Symbolics", \
    ]; \
    using Pkg; \
    Pkg.add(packages);'

# Install Python requirements
USER root
RUN pip install jupyterlab jupyterlab_server pandas matplotlib xarray numpy poetry scipy

# Install project requirements
COPY --chown=1000:1000 pyproject.toml poetry.lock /jupyter
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

# Kernel hast to go in a specific spot
COPY llmkernel /usr/local/share/jupyter/kernels/llmkernel

# Copy src code over
RUN chown 1000:1000 /jupyter
COPY --chown=1000:1000 . /jupyter

# Switch to non-root user
USER 1000

CMD ["python", "main.py", "--ip", "0.0.0.0"]

