#!/usr/bin/env -S julia --threads=4 --startup=no --color yes

INCLUDED_SYSIMAGES_PACKAGES = [
    "ACSets",
    "AlgebraicRewriting",
    "CSV",
    "Catlab",
    "CombinatorialSpaces",
    "DataFrames",
    "DataStructures",
    "Decapodes",
    "DifferentialEquations",
    "DisplayAs",
    "GATlab",
    "GeometryBasics",
    "HTTP",
    "IJulia",
    "JLD2",
    "JSON3",
    "ModelingToolkit",
    "MultiScaleArrays",
    "OrdinaryDiffEq",
    "PackageCompiler",
    "Plots",
    "Pluto",
    "SciMLBase",
    "SymbolicUtils",
    "Symbolics",
    "SyntacticModels",
    "XLSX",
]
NEEDED_VERSION = v"1.9"
if VERSION < NEEDED_VERSION
    throw("Currently running Julia $VERSION but the ASKEM environment requires $NEEDED_VERSION")
end

import Pkg
Pkg.activate(".")

import PackageCompiler 

target = if !(length(ARGS) == 0) lowercase(ARGS[1]) else "local" end

sysimage_dir = "/"
env_dir = if target == "local"
    env_dir = homedir() * "/.julia/environments/askem/"
    sysimage_dir = env_dir
    if !isdir(env_dir)
        mkdir(env_dir)
    else
        @warn "An ASKEM environment is already installed.\n Would you like to overwrite your current ASKEM environment? [yes/no]"
        if lowercase(readline()) != "yes"
            @info "Canceling install..."
            exit()
        end
        @warn "Overwriting ASKEM environment...."
    end
    cp("Project.toml", env_dir * "Project.toml"; force=true) 
    cp("Manifest.toml", env_dir * "Manifest.toml"; force=true) 
    Pkg.activate(env_dir)
    env_dir
end

Pkg.instantiate()

PackageCompiler.create_sysimage(INCLUDED_SYSIMAGES_PACKAGES; precompile_execution_file="precompile.jl", sysimage_path=sysimage_dir*"ASKEM-Sysimage.so")
if target == "local"
    @info """
        To use the basic (slower) mode, simply run:
        ```
        julia # enter the Julia Repl
        julia> ] activate @askem
        ```
    
        If you wish to start using the sysimage (optimized/faster) mode:
        ```
        julia --project="@askem" --startup=no --color yes -J$(env_dir)ASKEM-Sysimage.so
        ```
    """
end