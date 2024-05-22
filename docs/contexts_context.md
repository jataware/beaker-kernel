---
layout: default
title: Context class
parent: Contexts
nav_order: 1
has_toc: true
---

# Context class

A context is specified by inheriting from the `BaseContext`.


```python
from beaker_kernel.lib.context import BaseContext

class FooContext(BaseContext):
  ...
  
```


There are certain methods you that modify the behavior of the context
- `setup`: This method is executed when the context starts. When a new context is selected, first the new subkernel is created.
   Then the context is initialized. Finally, the setup code is generated once the subkernel and context exist.
- `auto_context`: This provides a dynamic context to the agent. The contents are generated for each query made.
- `post_execute`: Code that runs every time code is executed on the subkernel. This can be used for logging
   or sending previews to the UI.

```python
from beaker_kernel.lib.context import BaseContext

class FooContext(BaseContext):
  ...

  async def setup(self, context_info, parent_header):
    value = context_info.get("important_var")
    self.execute(f"important_var = {value}")
    # now `important_var` will preexist in the user's session

  async def auto_context(self):
    from datetime import datetime
    return f"You are an agent helping the user in the notebook. The current {datetime.now()}"
    

  async post_execute(self, message):
    logging.info("Code executed")
    self.send_preview(parent_header=message.parent_header)
    ...
  
```

