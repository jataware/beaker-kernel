FROM julia:1.9

RUN apt update && \
    apt install -y clang jupyter && \
    apt clean -y

ENV JULIA_DEPOT_PATH=/usr/local/julia
ENV JULIA_PROJECT=/

WORKDIR /
COPY Project.toml Project.toml
COPY Manifest.toml Manifest.toml
RUN julia -e 'using Pkg; Pkg.instantiate()'
COPY install.jl install.jl
COPY precompile.jl precompile.jl
RUN ./install.jl docker
RUN julia -e 'using Pkg; using IJulia; IJulia.installkernel("Julia ASKEM"; julia=`julia --project=/ --threads=4 -J/ASKEM-Sysimage.so`)'

EXPOSE 8888
EXPOSE 1234

# CMD julia -JASKEM-Sysimage.so --threads=4 -e 'using Pkg; Pkg.activate("/"); using Pluto; Pluto.run(;host="0.0.0.0", port=1234, launch_browser=true)'
CMD jupyter notebook --ip 0.0.0.0 --allow-root --no-browser
