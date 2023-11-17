# Standard ASKEM Julia Environment
This repo specifies packages developed or used by the ASKEM program. Additionally,
this environment can be installed locally or through Docker and provides optional hosting for
IJulia and Pluto.

## Installation
### Local
```
./install.jl
```

### Docker
```
docker build . -t julia-env:latest
```


## Usage

### Local

To use the basic (slower) mode, simply run:
```
julia # enter the Julia Repl
julia> ] activate @askem
```

If you wish to start using the sysimage (optimized/faster) mode:
```
julia --project="@askem" --startup=no --color yes -J{$HOME}/.julia/environments/askem/ASKEM-Sysimage.so
```

### Docker 

```
docker run -p 8888:8888 julia-env
```
