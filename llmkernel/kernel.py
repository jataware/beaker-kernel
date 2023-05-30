import json
import traceback

from ipykernel.kernelbase import Kernel
from ipykernel.ipkernel import IPythonKernel
from chatty.datasets.dataset_toolset import DatasetToolset
from archytas.react import ReActAgent

class PythonLLMKernel(Kernel):
    implementation = "askem-chatty-py"
    implementation_version = "0.1"
    banner = "Chatty ASKEM"

    language_info = {
        "mimetype": "text/plain",
        "name": "text",
        "file_extension": ".txt",
    }


    def setup_instance(self, *args, **kwargs):
        # Init LLM agent
        self.toolset = DatasetToolset()
        self.agent = ReActAgent(tools=[self.toolset], allow_ask_user=False, verbose=True)
        self.toolset.agent = self.agent
        if getattr(self, 'context', None) is not None:
            self.agent.clear_all_context()
        self.context = None
        self.msg_types.append("context_setup_request")
        return super().setup_instance(*args, **kwargs)


    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False, *, cell_id=None):
        # Send "code" to LLM Agent. The "code" is actually the LLM query
        try:
            result = self.agent.react(code)
        except Exception as err:
            error_text = f"""LLM Error: 
{err}

{traceback.format_exc()}
"""
            stream_content = {"name": "stderr", "text": error_text}
            self.send_response(self.iopub_socket, "stream", stream_content)
            return {
                "status": "error",
                "execution_count": self.execution_count,
                "payload": [],
                'user_expressions': {},
            }
        
        try:
            data = json.loads(result)
            if data.get("action") == "code_cell":
                stream_content = {"language": data.get("language"), "code": data.get("content")}
                self.send_response(self.iopub_socket, "code_cell", stream_content)
        except json.JSONDecodeError:  # If response is not a json, it's just text so treat it like text
            if not silent:
                stream_content = {"name": "response_text", "text": f"{result}"}
                self.send_response(self.iopub_socket, "chatty_response", stream_content)

        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            'user_expressions': {},
        }

    def set_context(self, context, context_info):
        match context:
            case "dataset":
                dataset_id = context_info["id"]
                print(f"Processing dataset w/id {dataset_id}")
                self.toolset.set_dataset(dataset_id)
                self.context = self.agent.add_context(self.toolset.context())

    def send_response(self, stream, msg_or_type, content=None, ident=None, buffers=None, track=False, header=None, metadata=None, channel="shell"):
        # Parse response as needed
        return super().send_response(stream, msg_or_type, content, ident, buffers, track, header, metadata, channel)

    async def context_setup_request(self, queue, message_id, message, **kwargs):
        # TODO: Set up environment for kernel
        # Basically, run any code/import any files needed for context

        content = message.get('content', {})
        context = content.get('context')
        context_info = content.get('context_info', {})

        if content:
            self.set_context(context, context_info)

        self.send_response(
            stream=self.iopub_socket, 
            msg_or_type="status", 
            content={
                "execution_state": "idle",
            },
            channel="iopub"

        )

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=PythonLLMKernel)
