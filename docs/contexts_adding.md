---
layout: default
title: Adding a new Context
parent: Contexts
nav_order: 2
has_toc: true
---

# Adding a new Context

Adding a new context is as simple as installing your context as a regular python library and adding a JSON file to one of a specific set of directories, similar to how Jupyter kernels are installed. Like Jupyter kernels, the context json file is added to a shared library location on the filesystem.

Upon startup, Beaker will review the preset locations for any installed Beaker contexts. If a context is found, it will be automatically registered and be able to be used. If more than one context is found with the same slug id, then the most specific version will be found, that is: a per-user install will take precedence over a system-wide install.


### Context json file format

```js
{
    "slug": string, // A unique short string name used to identify your context. Should be the same as what is set when setting a context in Beaker kernel
    "package": string, // A dot-seperated import path string to the package module that contains the [Context class](contexts_context.md)
    "class_name": class_name, // The case sensitive name of the Beaker context class that can be imported in the package listed above.
}
```

### Context json file search locations

#### Linux:
 * /usr/share/beaker
 * /usr/local/share/beaker
 * {sys.prefix}/share/beaker
 * ~/.local/share/beaker
 * {os.environ["XDG_DATA_HOME"]}/beaker

#### Mac OSX:

 * /usr/share/beaker
 * /usr/local/share/beaker
 * ~/.local/share/beaker
 * ~/Library/Beaker

#### Windows:
 * %PROGRAMDATA%\beaker
 * %APPDATA%\beaker
 * %LOCALAPPDATA%\beaker
