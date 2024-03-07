# beaker-ts typescript library

Beaker-ts is a typescript library that simplifies working with Beaker in the
browser. Highlights of what beaker-ts provides include:

* Easy creation of Beaker sessions
  * Connecting to an existing Beaker kernel or spinning up a new one
  * Ability to send/recieve messages directly to the Beaker kernel
  * Kernel status tracking
* A light-weight reactive notebook
  * Interfaces and classes for all standard Jupyter cells
  * A new Beaker "LLM Query" cell for interactions with the LLM agent
  * Full rendering of types registered with Jupyter
  * Exportable to a standard Jupyter .ipynb file
  * Tested to be reactive in React and Vue frameworks
* Session history tracking
  * Tracks all actions taken in a notebook (in progress)
  * Savable/Exportable to JSON (coming soon)
  * Ability to fully roll-back a notebook to a previous point (planned feature)

It is recommended to use the beaker-ts library to create and edit your Beaker
sessions and notebooks.


