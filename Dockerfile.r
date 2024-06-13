FROM python:3.10
RUN useradd -m jupyter
EXPOSE 8888

RUN apt update && apt install -y lsof

# Install R
RUN apt update && \
    apt install -y r-base r-cran-irkernel && \
    apt clean -y && \
    apt autoclean -y \
    apt autoremove -y

ENV MAKE="make -j4"

# Install forecast hub requirements (Rlang)
RUN R -e "install.packages(c('evalcast', 'covidcast', 'magrittr', 'lubridate'), repos='http://cran.rstudio.com/')"
RUN R -e "remotes::install_github('cmu-delphi/covidcast', ref = 'main', subdir = 'R-packages/evalcast')"

# Install Python requirements
RUN pip install --upgrade --no-cache-dir hatch pip

# Install project requirements
COPY --chown=1000:1000 pyproject.toml README.md hatch_build.py /jupyter/

# Hack to install requirements without requiring the rest of the files
RUN pip install --no-cache-dir -e /jupyter

# Copy src code over
COPY --chown=1000:1000 . /jupyter
RUN chown -R 1000:1000 /jupyter
RUN pip install --no-cache-dir /jupyter

# Switch to non-root user. It is crucial for security reasons to not run jupyter as root user!
USER jupyter
WORKDIR /jupyter

# Service
CMD ["beaker", "notebook", "--ip", "0.0.0.0"]
