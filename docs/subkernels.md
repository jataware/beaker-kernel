---
layout: default
title: Subkernels
nav_order: 5
has_toc: true
---

# Subkernels

A Beaker subkernel is an ordinary Jupyter kernel, but that is spawned by, and
controlled by the Beaker kernel rather than the front-end notebook interface.
The subkernel has a distinct environment which persists in the same way as a
normal notebook kernel.

Communication with the subkernel is performed by proxying messages through the
Beaker kernel. The front-end should only know of the existence of the Beaker
kernel, even though there is a second kernel behind the scenes.


## subkernel library files


The subkernel files within the lib directory are required to define some common
behaviours and provide a function for Beaker to behave consistently and properly
parse the responses from subkernel executions.

The main issue that there is no consistent way between Jupyter kernels for how
to bubble up the return value from a code cell. As the Beaker kernel evaluates
expressions in the subkernel environment, we need a consistent way to interpret
what is returned.

For most languages, this means serializing the response to JSON or another
interchange format. But beyond this, the R kernel does not send a
execute_response message, so to evaluate the response, we must capture and parse
the stdout text.

## Adding a subkernel

A subkernel can registered and added similarly as to how a context is. That is,


### Subkernel json file structure

```js
{
    "slug": string, // A unique short string name used to identify your subkernel.
    "package": string, // A dot-seperated import path string to the package module that contains the subkernel class definition.
    "class_name": class_name, // The case sensitive name of the subkernel class that can be imported from the package listed above.
}
```

### Subkernel json file search locations

#### Linux:
 * /usr/share/beaker/subkernels
 * /usr/local/share/beaker/subkernels
 * {sys.prefix}/share/beaker/subkernels
 * ~/.local/share/beaker/subkernels
 * {os.environ["XDG_DATA_HOME"]}/beaker/subkernels

#### Mac OSX:

 * /usr/share/beaker/subkernels
 * /usr/local/share/beaker/subkernels
 * ~/.local/share/beaker/subkernels
 * ~/Library/Beaker/subkernels

#### Windows:
 * %PROGRAMDATA%\beaker/subkernels
 * %APPDATA%\beaker/subkernels
 * %LOCALAPPDATA%\beaker/subkernels
