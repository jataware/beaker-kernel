---
layout: default
title: Previews
parent: Contexts
nav_order: 4
has_toc: true
---

# Previews

Contexts can optionally return previews to indicate the state inside the
context.

The preview can return multiple representations of the state for any number of
items needing preview.

## Adding a preview to your context

Add a generate_preview() function!

## Format of a preview payload

```javascript
{
  <item_type>: {
    <item_name>: {
      <mimetype>: <any json-encodable content>
    }
  }
}
```

**Example:**
```javascript
{
    "datasets": {
        "hospitals": {
            "application/json": [
                [...],
                [...],
                [...]
            ],
            "text/html": "<table><tr>...</table>",
            "text/plain": "hosp_id,hosp_name,hosp_city_id,..."

        },
        "cities": {
            "application/json": [[...],[...],[...]],
            "text/html": "<table><tr>...</table>",
            "text/plain": "id,name,state,..."
        },
        "doctors": {
            "application/json": [[...],[...],[...]],
            "text/html": "<table><tr>...</table>",
            "text/plain": "doctor_id,doctor_name,doctor_hosp_id,..."
        }
    },
    "maps": {
        "arlington_va": {
            "image/jpeg": "/9j/4AAQSkZJRg...RQB//2Q==",
            "text/plain": "Map of Arlington, VA"
        },
        "washington_dc": {
            "image/jpeg": "/9j/4AAQSkFikk...vRn//2Q==",
            "text/plain": "Map of Washington, DC"
        }
    },
    "pins": {
        "pins": {
            "application/x-doctor-location": [
                {
                    "lat": -77.0361691,
                    "lon": 38.9049533,
                    "doctor_id": 4335,
                },
                {
                    "lat": -77.0437808,
                    "lon": 38.9048841,
                    "doctor_id": 8146,
                },
                {
                    "lat": -77.0496311,
                    "lon": 38.9200379,
                    "doctor_id": 2380,
                }
            ]
        }
    }
}
```


### Item types

This is a unique identifier for the type of item being previewed. Either
displayed or used as a selection criteria as needed.

Useful for grouping like items together if more than one type of item is being
previewed.


### Item names

This is a unique name of the item being previewed and should be identifiable by
the user. Usually this will be a variable name for a local variable type.


### MIME Types

A [MIME Type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types)
indicator the determines how the preview should be rendered.

You can provide your own mimetype if you also create a renderer for it.

#### The following MIME Types have renderers built in provide by Jupyter:

* text/plain
* text/html
* text/markdown
* image/bmp
* image/png
* image/jpeg
* image/gif
* image/webp
* image/svg+xml
* text/javascript
* application/javascript
* application/vnd.jupyter.stdout  ( Custom Jupyter type )
* application/vnd.jupyter.stderr  ( Custom Jupyter type )

#### These MIME Types have renderers defined in the Beaker-vue library

* text/latex
* application/latex
* text/json
* application/json

<br/>

## Adding a new renderer
