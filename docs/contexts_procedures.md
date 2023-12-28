---
layout: default
title: Code
parent: Contexts
nav_order: 3
has_toc: true
---

# Procedures

One of the strengths of Beaker is that it can execute code in the subkernel, and
use the results/output of that code in Beaker itself.

This is accomplished by use of "procedures", snippets of code that are executed
in the subkernel environment, as if it were run in a notebook cell.

Procedures exist at the context level, and are tied to that particular context.
A single procedure can be used for multiple subkernels if the context is
designed to handle them.

Procedure files are actually
[Jinja2 templates](https://jinja.palletsprojects.com/en/2.11.x/), which are
rendered at usage to generate the code that is to be exectued. This allows one
to provide "virtual arguments" in the form of template substitutions or
rendering prior to the code being run.

## Procedure definition

The directory which holds the context class definition file should also contain
a directory named `procedures`. In this directory should be one or more
sub-directories whose names match a subkernel slug name. Inside the subkernel
folder, you should place your procedure template files.

A procedure's name should match the filename, minus any extension. For
convenience, the extension of the language used is often used. I.e. `.py` for
Python files, `.jl` for Julia, etc.
