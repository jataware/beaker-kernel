---
layout: default
title: Integrations
nav_order: 5
has_toc: true
has_children: true
---

# Integrations -- Overview

Integrations are Beaker's faculty for creating wrappers around external datasources and tools of different varieties that may, but do not necessarily require the use of, a second agent's context. Integrations are meant to be flexible and cover some of the ground of a general plugin system in Beaker.

At a high level, an integration could be...
* A remote or local web API
* A remote or local dataset or database
* A code library or suite of tools for doing domain specific work where additional documentation would be useful to the agent
* Some form of tools, such as use with MCP servers (not yet implemented)
* Agent-to-agent communication (not yet implemented)

Integrations fit into Beaker with the following architecture.

**Contexts** have a list of **Integration Providers** defined, that are responsible for enumerating their own **Integrations** and providing a base set of functionality. **Integrations** have associated **Resources** for supplemental, necessary information.

The integration functionality is exposed behind a REST API for communication. [More details can be found here.](integrations_api.html)

## Integration Providers

On a given context, the `integrations` field will hold a list of providers (any object inheriting `BaseIntegrationProvider` or `MutableBaseIntegrationProvider`). If this field is empty or `[]`, no integrations details will be shown to the user as the feature is effectively disabled in the frontend.

At minimum, an integration provider is responsible for the following:

```python
def list_integrations(self) -> list[Integration]:
    ...

def get_integration(self, integration_id: str) -> Integration:
    ...

def list_resources(self, integration_id: str, resource_type: Optional[str] = None) -> list[Resource]:
    ...

def get_resource(self, integration_id: str, resource_id: str) -> Resource:
    ...
```

as well as their name, which is set at initialization (`super().__init__(display_name)`) to inform the context about the provider.

Providers that are mutable, inheriting `MutableBaseIntegrationProvider`, that are designed to have integrations added and updated at runtime, will have more to implement for the usual add/update/delete methods as well.

`beaker_kernel/lib/integrations/base.py` contains the relevant information.

How integrations are stored and used, as well as prompt management, *are up to the provider itself*:

### Provider Prompts

If no prompt is set, the provider's docstring + string representations of the integrations will be used as a default.

Overriding the provider prompt for prompt management reasons can be done via the following ways:

1) Setting `prompt_instructions` on the provider, which will be added to the above, or

2) Overriding the prompt, as shown below:

```python
@property
def prompt(self) -> str:
    ...
```

This custom prompt will be injected to the context and updated in place to track the output of the prompt property.

### Provider Tools

Functions that are decorated with @tool (see tools in contexts elsewhere in documentation) will be added to the agent when the context is loaded, and those tools have access to the provider's self binding and can use/interact with however integrations are stored.

At a glance:

* Provider lists integrations to Context
* Agent reads integrations list and interacts via Provider's tools based on query

## Integrations

Integrations are implementation dependent and defined on the context, but a general structure for usability is defined.

```python
name: str
description: str
provider: str
resources: dict[str, Resource]
uuid: str
source: str
slug: str # (machine readable version of name)
datatype: "api" | "database" | "dataset"
url: str
img_url: str
last_updated: datetime | date
```

`beaker_kernel/lib/types.py` contains the relevant information for Integrations and their typing.

## Resources

Resources are anything inheriting `Resource`, which only contains the following:

* `resource_type`, a ClassVar defined on subclasses
* `resource_id`, a UUID
* `integration`, the UUID of the parent that owns the resource

and specialized subclasses for files and agent query examples extend these to have their own extended information.

`beaker_kernel/lib/types.py` contains the relevant information for Resources and their typing.
