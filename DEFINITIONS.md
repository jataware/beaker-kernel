# Definitions

### The beaker repo consists of three libraries:
1. beaker_kernel: Python module
1. beaker-ts: Contoller and Model library for intermediary representations of the application state.
1. beaker-vue: VueJs based component library with a several built-in pages for immediate use.


## beaker_kernel
> Python library that provides both the Beaker kernel for Jupyter and a customized back-end for serving/using Beaker notebooks.
> ...

### Kernel

### Subkernel

### ProxyKernel

### Agent

### Context


## beaker-ts (maybe rename to beaker-lib or other better name?)
> TS/JS classes that provide data and methods to manipulate the data

### Model
> A class or other structure whose purpose is to store data that represents a current state.  
> MUST be serializable to JSON.  
> MAY contain methods or other logic.  
> MUST be ["reactive"](https://vuejs.org/guide/extras/reactivity-in-depth.html) so that they play nicely with VueJs and ReactJs.  

### Controller
> A class or other structure that collects references to, and functionality to interact with, services, models, and similar external (to the controller) resources.  
> DOES NOT need to be serializable to JSON.  


### SessionController
> Single [controller] that holds references to all other controllers, models, and services for a "session".  
> 

### BeakerNotebookModel
> A simplified, reactive representation of [Jupyter Notebook](http://link-to-jupyter-docs/).  


### Cell - BeakerCellModel

### Raw Cell - BeakerRawCellModel

### Code Cell - BeakerCodeCellModel

### Markdown Cell - BeakerMarkdownCellModel

### Query Cell - BeakerQueryCellModel



## beaker-vue
> Vue components that exist as JS objects during page rendering/interaction.  
> Standard set of overridable / extendable components rather than just one UI workflow.  
> Can be composed and extended into new pages.  

### Component


### Widget


### Session

### notebook
> A widget that contains cells and handles interactions between the cells and the session.  

### Cell - BeakerVueCell

### Raw Cell - BeakerVueRawCell

### Code Cell - BeakerVueCodeCell

### Markdown Cell - BeakerVueMarkdownCell

### Query Cell - BeakerVueQueryCell



## Responsibility of handling updates between layers
 - Any action/modification that originates in the Vue layer should be handled as much as possible in the vue layer.
 - Each vue component MAY have ownership of a single model/component.
 - If a Vue component does have ownership of a model/component, all changes to the owned entity MUST be made via the component.
 - Unless otherwise defined, Vue components DO NOT own their own the children of owned entities. Instead the Vue components for the child entities MUST exist such that each child is owned by a distinct Vue component.
 - If a component needs to modify/interact with a child entity, it MUST do so through the Vue component and not interact with the model/controller that is owned by another component.
 - A components may call functions/methods on, or traverse over non-owned models/controllers as long as no changes are being made. (E.g. search, checking status of a parent/child, etc).


## Reserved terminology

The following terms are reserved and should not be reused/recontextualized/extended or otherwise given any new meanings/usages:

 - Agent
 - Cell
 - Context
 - History
 - Kernel
 - Notebook
 - Render
 - Session
 - Subkernel
