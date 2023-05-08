import traceback

from ipykernel.kernelbase import Kernel
from chatty.controller import Controller
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
        self.agent = ReActAgent(tools=[Controller()], allow_ask_user=False, verbose=True)
        self.msg_types.append("context_setup_request")
        return super().setup_instance(*args, **kwargs)


    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False, *, cell_id=None):
        # Send "code" to LLM Agent. The "code" is actually the LLM query
        print(self.msg_types)
        print(self.shell_handlers)
        try:
            # result = self.agent.react(code)
            print(code)
            result = ''
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
        # print("\n".join(dir(self.agent)))
        # self.agent.prompt 
        match context:
            case "dataset":
                dataset_id = context_info["id"]
                print(f"Processing dataset w/id {dataset_id}")

    def send_response(self, stream, msg_or_type, content=None, ident=None, buffers=None, track=False, header=None, metadata=None, channel="shell"):
        # Parse response as needed
        return super().send_response(stream, msg_or_type, content, ident, buffers, track, header, metadata, channel)

    async def context_setup_request(self, queue, message_id, message, **kwargs):
        # TODO: Set up environment for kernel
        # Basically, run any code/import any files needed for context
        import pprint
        print(pprint.pformat(message))

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
