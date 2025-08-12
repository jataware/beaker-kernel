# Archytas to LangGraph Migration Guide

## Overview

This document details the complete migration from Archytas to LangGraph in beaker-kernel. The migration eliminates all Archytas dependencies and replaces them with a modern, pure LangGraph implementation while maintaining full backward compatibility and enhanced functionality.

## Migration Results

**Successfully Completed:**
- **Zero Archytas Dependencies**: Completely eliminated legacy framework
- **Custom LangGraph Architecture**: Modern agent system with custom graph for thought extraction
- **Thought Extraction System**: Real-time thought extraction and UI communication before tool execution
- **Standard ToolNode**: Uses LangGraph's standard ToolNode for reliable tool execution
- **Custom Chat History**: `BeakerChatHistory` optimized for Beaker's UI and auto-summarization
- **Native Tool System**: LangChain `@tool` decorator with proper logging (`agent_react_tool` events)
- **Full UI Compatibility**: Chat history panel, tool logging, and thought display work correctly
- **Enhanced Performance**: Direct LangGraph integration without compatibility layers

## Architecture Changes

### Before (Archytas-based)
```
beaker_kernel/
├── lib/
│   ├── agent.py              # ReActAgent wrapper (Archytas)
│   ├── utils.py              # Archytas imports and utilities
│   └── config.py             # Archytas model discovery
└── contexts/default/
    ├── agent.py              # @tool with AgentRef/LoopControllerRef
    └── context.py            # Uses Archytas BeakerAgent
```

### After (LangGraph-based)
```
beaker_kernel/
├── lib/
│   ├── agent.py              # BeakerAgent (custom LangGraph with thought extraction)
│   ├── tools.py              # Native LangChain @tool decorator system  
│   ├── chat_history.py       # Custom BeakerChatHistory with UI integration
│   └── config.py             # Direct LangChain model configuration
└── contexts/default/
    ├── agent.py              # DefaultAgent + native tools
    └── context.py            # Uses DefaultAgent
```

## Detailed Implementation Changes

### 1. Core Agent System

#### Custom LangGraph with Thought Extraction

**Architecture**: The agent uses a custom LangGraph instead of `create_react_agent()` to enable real-time thought extraction:

```
agent → extract_thoughts → tools → agent
```

**Flow**:
1. **Agent Node**: Model generates response with tool calls
2. **Extract Thoughts Node**: Intercepts response, sends thoughts to UI via `llm_thought` events
3. **Tools Node**: Standard ToolNode executes valid tool calls  
4. **Back to Agent**: Process tool results and continue or finish

**Thought Extraction Features**:
- **Real-time UI Updates**: Thoughts appear in UI immediately, before tool execution
- **Multi-provider Content Handling**: Supports both Anthropic (list) and OpenAI (string) content formats
- **Malformed Call Filtering**: Skips thought extraction for empty `run_code` calls to prevent UI spam
- **Preserves Formatting**: Line breaks and formatting preserved from AI responses

**Implementation**:
```python
def _extract_thoughts_node(self, state: MessagesState):
    \"\"\"Extract thoughts from tool calls and send to UI.\"\"\"
    if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls'):
        ai_content = self._extract_ai_content(last_message)
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get('name', 'unknown_tool')
            args = tool_call['args']
            
            # Skip malformed calls (prevents infinite "Calling tool run_code")
            if not self._should_extract_thought_for_tool(tool_name, args):
                continue
                
            # Send thought to UI
            self._send_thought_to_ui(ai_content, tool_name, str(args))
```

#### File: `beaker_kernel/lib/agent.py`
- **Before**: Wrapper around Archytas `ReActAgent`
- **After**: Custom LangGraph `BeakerAgent` with thought extraction and standard ToolNode execution

**Key Changes**:
```python
# OLD (Archytas) - Original Implementation
from archytas import ReActAgent

class BeakerAgent(ReActAgent):
    def __init__(self, model, tools, **kwargs):
        super().__init__(model=model, tools=tools, **kwargs)

# NEW (LangGraph) - Custom Implementation with Thought Extraction
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState
from beaker_kernel.lib.chat_history import BeakerChatHistory

class BeakerAgent:
    def __init__(self, context=None, tools=None, **kwargs):
        self.model = config.get_model() or DefaultModel({})
        self.chat_history = BeakerChatHistory(model=self.model)  # Custom implementation
        self._langgraph_app = self._create_thought_extracting_graph()  # Custom graph!
        
    def _create_thought_extracting_graph(self):
        # Custom graph: agent → extract_thoughts → tools → agent
        workflow = StateGraph(MessagesState)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("extract_thoughts", self._extract_thoughts_node)  
        workflow.add_node("tools", ToolNode(self._tools))  # Standard ToolNode
        # ... routing logic for thought extraction
```

#### Custom LangGraph Architecture Decision
- **Custom Graph**: Built thought-extracting graph instead of using `create_react_agent()`
- **Why Custom Graph?**: 
  - **Thought Extraction**: Intercepts AI responses before tool execution to send thoughts to UI
  - **Real-time UI Updates**: Sends `llm_thought` events to frontend during agent reasoning
  - **Malformed Call Filtering**: Prevents infinite "Calling tool run_code" spam from Claude's empty calls
  - **Multi-provider Support**: Handles different content formats (Anthropic list vs OpenAI string)
  - **Standard Tool Execution**: Uses reliable ToolNode for actual tool execution

#### Chat History Architecture Decision
- **Custom Implementation**: Built `BeakerChatHistory` instead of using LangGraph's built-in memory
- **Why Custom?**: 
  - **UI Integration**: Beaker's frontend requires specific data formats and token calculations
  - **Auto-summarization**: Custom logic for model-specific context window management
  - **Backward Compatibility**: Maintains existing chat history panel functionality
  - **Performance**: Optimized for Beaker's specific use cases and UI requirements

### 2. Tool System

#### File: `beaker_kernel/lib/tools.py` (NEW)
- **Before**: Archytas `@tool` decorator from `archytas.tool_utils`
- **After**: Native LangChain `@tool` decorator with execution context

**Migration Example**:
```python
# OLD (Archytas) - Original Implementation
from archytas.tool_utils import tool

@tool()
async def my_tool(param: str, agent: AgentRef, loop: LoopControllerRef) -> str:
    context = await agent.context.evaluate(code)
    return context["return"]

# NEW (LangGraph) - Pure Implementation with Proper Logging
from beaker_kernel.lib.tools import tool

@tool
async def my_tool(param: str) -> str:
    kernel = get_beaker_kernel()
    context = await kernel.context.evaluate(code)
    return context["return"]
```

**Tool Logging Integration**:
Our custom `@tool` decorator automatically logs tool invocations with the correct event names:
- `agent_react_tool`: Tool invocation with name and input parameters
- `agent_react_tool_output`: Tool completion with input, output, and timing

This ensures the Beaker UI displays properly formatted tool calls instead of raw JSON.

#### File: `beaker_kernel/lib/subkernel.py`
- **Updated**: `run_code` tool to use native `@tool` decorator
- **Removed**: Archytas parameter injection system
- **Maintained**: All execution context and notebook cell visibility

### 3. Model Configuration

#### File: `beaker_kernel/lib/config.py`
- **Before**: Archytas model discovery and instantiation
- **After**: Direct LangChain model instantiation

**Provider Mapping** (Archytas → LangChain):
| Old (Archytas) | New (LangChain) |
|---|---|
| `archytas.models.openai.OpenAIModel` | `langchain_openai.ChatOpenAI` |
| `archytas.models.anthropic.AnthropicModel` | `langchain_anthropic.ChatAnthropic` |
| `archytas.models.bedrock.BedrockModel` | `langchain_aws.ChatBedrock` |
| `archytas.models.gemini.GeminiModel` | `langchain_google_genai.ChatGoogleGenerativeAI` |

**Config File Update Required**:
```toml
# OLD ~/.config/beaker.conf
[providers.anthropic]
import_path = "archytas.models.anthropic.AnthropicModel"

# NEW ~/.config/beaker.conf  
[providers.anthropic]
import_path = "langchain_anthropic.ChatAnthropic"
```

### 4. Dependencies

#### File: `pyproject.toml`
```toml
# REMOVED
"archytas>=1.4.0"

# ADDED
"langgraph>=0.2.0"
"langchain-core>=0.3.0"  
"langchain-openai>=0.2.0"
"langchain-anthropic>=0.2.0"
```

### 5. Chat History and Summarization System

#### Modular Architecture Design
The chat history system uses a clean separation of concerns with pluggable summarization strategies:

```
beaker_kernel/lib/
├── chat_history.py              # Chat history management only
└── summarization/
    ├── __init__.py              # Factory and exports
    ├── base.py                  # Abstract base class
    ├── llm_summarizer.py        # LLM-powered summarization
    └── simple_summarizer.py     # Fallback strategy
```

#### File: `beaker_kernel/lib/chat_history.py` (Focused Chat History Management)
The `BeakerChatHistory` focuses solely on chat history management with pluggable summarization:

**Core Features**:
- **Model-aware Context Windows**: Automatic detection of context limits per model type
- **Pluggable Summarization**: Uses strategy pattern for different summarization approaches
- **UI Integration**: Perfect compatibility with Beaker's chat history panel
- **Token Management**: Accurate token counting and usage tracking
- **Message Threading**: Support for ReAct loop IDs and message relationships

**Clean Implementation**:
```python
class BeakerChatHistory:
    def __init__(self, max_tokens=None, summarization_threshold=0.8, model=None, summarization_strategy="archytas"):
        # Model-specific context window detection
        self.max_tokens = max_tokens or get_model_context_window(model)
        self.summarization_threshold = summarization_threshold
        
        # Pluggable summarization strategy
        self.summarizer = get_summarizer(summarization_strategy)
        
    async def auto_summarize(self):
        # Uses pluggable summarizer instead of embedded logic
        summary_content = await self.summarizer.summarize(messages_to_summarize)
```

#### File: `beaker_kernel/lib/summarization/llm_summarizer.py` (LLM-Powered Summarization)
The `LLMSummarizer` contains sophisticated LLM-powered summarization logic (ported from Archytas):

- **Prompt Templates**: Exact system and user prompts from Archytas Jinja templates
- **Message Formatting**: Same UUID-based message structure (`msg_00000001` format)
- **Tool Call Handling**: Preserves tool usage context in summaries
- **Output Format**: Same `[SUMMARIZED CONVERSATION]: Below is a summary of X messages:` structure
- **LLM Invocation**: Direct model calls matching Archytas behavior

**Architectural Benefits**:
```python
# Easy to switch strategies
agent = BeakerAgent(summarization_strategy="simple")  # For testing
agent = BeakerAgent(summarization_strategy="llm")     # Production default

# Backward compatibility maintained
agent = BeakerAgent(summarization_strategy="archytas")  # Maps to "llm"

# Easy to add new strategies
class CustomSummarizer(ChatHistorySummarizer):
    async def summarize(self, messages): ...
```

**Why Custom vs LangGraph Built-in Memory?**

| Aspect | LangGraph Built-in | BeakerChatHistory |
|------------|------------------------|----------------------|
| **UI Integration** | Generic format, requires adaptation | Native Beaker format with `OutboundChatHistory` |
| **Token Calculations** | Basic counting | Model-specific context windows + overhead estimates |
| **Auto-summarization** | Basic context management | **Pluggable strategies including ported Archytas logic** |
| **Frontend Compatibility** | Requires compatibility layer | Direct integration with existing UI components |
| **Performance** | General-purpose | Optimized for Beaker's specific workflows |
| **Extensibility** | Limited | **Strategy pattern allows multiple summarization approaches** |

**Context Window Detection**:
```python
def get_model_context_window(model) -> int:
    if 'claude-3' in model_name: return 200000
    elif 'gpt-4' in model_name: return 128000
    elif 'gemini-1.5' in model_name: return 1000000
    # ... etc
```

## Potential Issues & Mitigation

### 1. Configuration Migration

**Issue**: Existing config files still reference Archytas models  
**Symptoms**: `AttributeError: 'DefaultModel' object has no attribute 'bind_tools'`

**Solution**: Update all `.beaker.conf` files:
```bash
# Find all config files
find ~ -name ".beaker.conf" -o -name "beaker.conf" 2>/dev/null

# Update import paths from archytas.models.* to langchain_*
```

**Auto-Migration Script**: Consider creating a migration script for users.

### 2. Custom Agent Implementations

**Issue**: Third-party contexts extending old `BeakerAgent`  
**Risk Level**: **HIGH** - Will break custom contexts

**Breaking Changes**:
- `BeakerAgent` no longer inherits from `ReActAgent`
- No more `chat_history.records()` method (now `get_records()`)
- Tool signatures changed (no more `AgentRef`, `LoopControllerRef`)

**Migration Path**:
```python
# OLD custom agent
class MyAgent(BeakerAgent):  # Was ReActAgent
    @tool()
    async def my_tool(self, param: str, agent: AgentRef):
        return await agent.context.evaluate(code)

# NEW custom agent  
class MyAgent(BeakerAgent):  # Now pure LangGraph
    @tool
    async def my_tool(self, param: str):
        kernel = get_beaker_kernel()
        return await kernel.context.evaluate(code)
```

### 3. Tool Parameter Changes

**Issue**: Tools expecting Archytas parameters will fail  
**Risk Level**: **MEDIUM** - Affects custom tools

**Old Signature**:
```python
async def tool(param: str, agent: AgentRef, loop: LoopControllerRef, react_context: ReactContextRef)
```

**New Signature**:
```python  
async def tool(param: str)  # Use get_beaker_kernel() for context access
```

### 4. Chat History Format Changes

**Issue**: UI expecting different chat history structure  
**Risk Level**: **LOW** - Handled with compatibility layer

**Solution**: `OutboundChatHistory` provides full backward compatibility.

### 5. Model Context Window Detection

**Issue**: Unknown models default to 128k tokens  
**Risk Level**: **MEDIUM** - May cause premature summarization

**Solution**: 
- Extend `get_model_context_window()` for new models
- Monitor logs for unknown model warnings
- Consider fallback to LangChain's `modelname_to_contextsize()` where available


## Creating New Contexts

Creating a new context with LangGraph is very similar to the old Archytas approach. The main changes are just the imports and parameter handling:

### Tool Decorator - Almost Identical

```python
# OLD (Archytas) - Original Implementation
from archytas.tool_utils import tool

@tool()
async def my_tool(param: str, agent: AgentRef, loop: LoopControllerRef) -> str:
    context = await agent.context.evaluate(code)
    return context["return"]

# NEW (LangGraph) - Pure Implementation
from beaker_kernel.lib.tools import tool

@tool
async def my_tool(param: str) -> str:
    kernel = get_beaker_kernel()
    context = await kernel.context.evaluate(code)
    return context["return"]
```

### Agent Class - Very Similar

```python
# OLD (Archytas-based)
from beaker_kernel.lib.agent import BeakerAgent

class MyAgent(BeakerAgent):
    def __init__(self, context=None, tools=None, **kwargs):
        my_tools = [my_tool]
        super().__init__(context=context, tools=my_tools, **kwargs)

# NEW (LangGraph-based)
from beaker_kernel.lib.agent import BeakerAgent

class MyAgent(BeakerAgent):
    def __init__(self, context=None, tools=None, **kwargs):
        my_tools = [my_tool] 
        super().__init__(context=context, tools=my_tools, **kwargs)
```

### Key Differences

1. **Import path**: `archytas.tool_utils` → `beaker_kernel.lib.tools`
2. **Tool parameters**: Remove `agent`, `loop`, `react_context` parameters from tool functions
3. **Context access**: `agent.context.evaluate()` → `get_beaker_kernel().context.evaluate()`
4. **Tool decorator**: Remove parentheses - `@tool()` → `@tool`

The overall structure, patterns, and context creation process remain the same. Most existing contexts will need minimal changes beyond updating imports and removing the Archytas-specific parameters.

### Tool Methods vs Functions

**Important**: If your existing Beaker contexts define tools as **methods on the agent class** (which was common in Archytas), you have two migration options:

#### Option 1: Convert to Standalone Functions (Recommended)
```python
# OLD (Archytas method-based tools)
class MyAgent(BeakerAgent):
    def __init__(self, context=None, **kwargs):
        self.api_key = "secret"
        super().__init__(context=context, **kwargs)
    
    @tool()
    async def my_tool(self, param: str, agent: AgentRef) -> str:
        # Could access self.api_key
        return await agent.context.evaluate(code)

# NEW (Standalone function tools)
@tool
async def my_tool(param: str) -> str:
    kernel = get_beaker_kernel()
    return await kernel.context.evaluate(code)

class MyAgent(BeakerAgent):
    def __init__(self, context=None, tools=None, **kwargs):
        default_tools = [my_tool]
        super().__init__(context=context, tools=default_tools + (tools or []), **kwargs)
```

#### Option 2: Keep as Agent Methods (Advanced)
If you need to access instance variables or maintain method-based tools:

```python
# NEW (Method-based tools with factory pattern)
class MyAgent(BeakerAgent):
    def __init__(self, context=None, tools=None, **kwargs):
        self.api_key = "secret"  # Instance variables available
        
        # Create tools from methods
        my_tool = self._create_my_tool()
        default_tools = [my_tool]
        super().__init__(context=context, tools=default_tools + (tools or []), **kwargs)
    
    def _create_my_tool(self):
        """Factory method to create tool bound to this instance."""
        @tool
        def my_tool(param: str) -> str:
            # Can access self here!
            api_key = self.api_key
            kernel = get_beaker_kernel()
            return f"Used {api_key} to process {param}"
        
        return my_tool
```

**When to use each approach:**
- **Option 1 (Standalone)**: When tools don't need agent instance data
- **Option 2 (Methods)**: When tools need access to `self.variables` or agent state

See `beaker_kernel/lib/code_analysis/analysis_agent.py` for a real example of Option 2 in use.

## Modular Summarization System

### New Modular Architecture
```
beaker_kernel/lib/
├── chat_history.py              # Chat history management ONLY
└── summarization/               # Dedicated summarization module
    ├── __init__.py              # Factory and exports  
    ├── base.py                  # Abstract base class
    ├── llm_summarizer.py        # LLM-powered summarization
    └── simple_summarizer.py     # Fallback strategy
```

**Usage**:
```python
# Default LLM-powered summarization
agent = BeakerAgent()

# Simple summarization for testing
agent = BeakerAgent(summarization_strategy="simple")

# Easy to add custom strategies
class CustomSummarizer(ChatHistorySummarizer):
    async def summarize(self, messages): ...
```

This refactoring transforms the codebase from "functional but architecturally messy" to "clean, professional, and maintainable."


### Additional Files Migrated

#### File: `beaker_kernel/lib/code_analysis/analysis_agent.py`
- **Issue**: Still importing `from archytas.react import ReActAgent, tool, LoopController`
- **Solution**: Migrated to extend `BeakerAgent` with native `@tool` decorator
- **Changes**:
  ```python
  # OLD
  from archytas.react import ReActAgent, tool, LoopController
  from archytas.tool_utils import LoopControllerRef
  
  class AnalysisAgent(ReActAgent):
      @tool
      def code_analysis(self, analysis_list, loop: LoopControllerRef):
          loop.set_state(loop.STOP_SUCCESS)
  
  # NEW  
  from beaker_kernel.lib.agent import BeakerAgent
  from beaker_kernel.lib.tools import tool
  
  class AnalysisAgent(BeakerAgent):
      def _create_code_analysis_tool(self):
          @tool
          def code_analysis(analysis_list: list[dict]) -> str:
              self._analysis_result = analysis_objects
              self._stop_requested = True
  ```

#### File: `beaker_kernel/lib/agent_tasks.py`
- **Issue**: `Summarizer` class inheriting from `archytas.react.ReActAgent`
- **Solution**: Migrated to extend `BeakerAgent` with LangGraph message handling
- **Changes**:
  ```python
  # OLD
  from archytas.react import ReActAgent
  
  class Summarizer(ReActAgent):
      def __init__(self, notebook: dict = {}, **kwargs):
          super().__init__(model=config.LLM_SERVICE_MODEL, ...)
          self.add_context(context)
  
  # NEW
  from beaker_kernel.lib.agent import BeakerAgent
  from langchain_core.messages import HumanMessage
  
  class Summarizer(BeakerAgent):
      def __init__(self, notebook: dict = {}, **kwargs):
          super().__init__(context=None, tools=[], **kwargs)
          context_message = HumanMessage(content=context)
          self.chat_history.add_message(context_message)
  ```

#### File: `beaker_kernel/lib/templates/agent_file.py`
- **Issue**: Template generating Archytas-style agent code for new contexts
- **Solution**: Updated template to generate modern LangGraph-style code
- **Changes**:
  ```python
  # OLD Template
  from archytas.tool_utils import AgentRef, LoopControllerRef, ReactContextRef, tool
  
  class {agent_class}(BeakerAgent):
      @tool()
      async def my_tool(self, param: str, agent: AgentRef, loop: LoopControllerRef):
  
  # NEW Template
  from beaker_kernel.lib.tools import tool
  from beaker_kernel.lib.agent import BeakerAgent
  
  @tool
  async def my_tool(param: str) -> str:
  
  class {agent_class}(BeakerAgent):
      def __init__(self, context=None, tools=None, **kwargs):
          default_tools = [my_tool]
          super().__init__(context=context, tools=default_tools + (tools or []), **kwargs)
  ```

### Legacy Code Cleanup

#### File: `beaker_kernel/kernel.py`
- **Removed**: 40+ lines of legacy Archytas chat history fallback code
- **Simplified**: Removed defensive `hasattr` checks that are no longer needed
- **Updated**: Comments to reflect current LangGraph-only architecture

#### File: `README.md`
- **Updated**: Framework attribution from Archytas to LangGraph
- **Modernized**: Technology description to reflect current implementation

### Verification Results

**Zero Archytas References**: Comprehensive scan confirms no remaining Archytas imports in Python code  
**All Components Tested**: `AnalysisAgent`, `Summarizer`, and template generation all working correctly  
**Template Generation**: New contexts will automatically use LangGraph patterns  
**Clean Architecture**: No legacy fallback code, compatibility layers, or outdated comments

## Post-Migration Refinements and Bug Fixes

### Critical Bug Fix: Conversation History Not Passed to Agent

**Issue Discovered**: After initial migration, the agent was responding with "I don't have access to our conversation history" because chat history wasn't being passed to LangGraph.

**Root Cause**: The `react_async` method was only passing the current user message instead of full chat history:
```python
# BROKEN: Only current message
messages = [user_message]  # Agent had no conversation context!
```

**Solution**: Updated to pass complete chat history:
```python
# FIXED: Full conversation context
all_messages = self.chat_history.messages.copy()  # Agent has full context
```

**Impact**: Agent now maintains conversation context and can reference earlier interactions.

### Bug Fix: Empty Message Content Validation

**Issue**: API errors due to empty message content violating provider requirements:
```
Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages.7: all messages must have non-empty content'}}
```

**Solution**: Added two-layer validation:
1. **Prevention**: `BeakerChatHistory.add_message()` validates and rejects empty messages
2. **Filtering**: `react_async()` filters out any existing empty messages before sending to LangGraph

```python
# Validation in add_message()
content = getattr(message, 'content', '')
if not content or not str(content).strip():
    logger.warning(f"Skipping message with empty content: {type(message).__name__}")
    return str(uuid4())  # Don't store empty messages

# Runtime filtering in react_async()
for msg in self.chat_history.messages:
    content = getattr(msg, 'content', '')
    if content and content.strip():
        all_messages.append(msg)
```

### Improved Response Message Handling

**Issue**: Complex message slicing logic was causing response messages to be lost or duplicated.

**Solution**: Simplified to extract the last message from LangGraph response:
```python
# Simplified approach
if "messages" in result and result["messages"]:
    last_message = result["messages"][-1]  # AI response is always last
    if isinstance(last_message, AIMessage):
        response_content = last_message.content
        if last_message not in self.chat_history.messages:  # Avoid duplicates
            self.chat_history.add_message(last_message, loop_id)
```
