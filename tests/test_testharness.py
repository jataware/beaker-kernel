import asyncio
import logging
import pytest
import requests
import sys
import time
import urllib.parse

from .harness import TestServer, TestKernelConnection, server, kernel_connection, kernel


logger = logging.getLogger()

class TestHarness:

    async def test_server(self, server):
        url = server.url('/api')
        req = requests.get(url)
        assert req.status_code == 200
        assert req.json()

    async def test_config_api(self, server):
        url = server.url('/config')
        req = requests.get(url)
        response = req.json()

        assert req.status_code == 200
        assert response
        assert 'appUrl' in response

    async def test_create_session_api(self, server):
        url = server.url('/api/sessions')
        req = requests.post(
            url,
            json={
                "kernel": {
                    "name": "beaker_kernel",
                },
                "path": "/test",
                "type": None,
            },
            headers={"Authorization": f"token {server.base_app.serverapp.token}"}
        )
        response = req.json()
        assert req.status_code == 201
        assert response
        assert 'id' in response
        assert 'kernel' in response
        assert response["kernel"]["name"] == "beaker_kernel"


    async def test_kernel_connection(self, server):
        # Create a kernel
        conn = await TestKernelConnection.new(server, "harness-test")
        assert conn
        assert conn.km.has_kernel

        # Destroy the kernel
        await conn.destroy()
        assert not conn.km.has_kernel


    async def test_kernel_fixture(self, kernel_connection):
        assert isinstance(kernel_connection, TestKernelConnection)
        assert kernel_connection.km.has_kernel
        assert kernel_connection.km.ports

    async def test_shell_message(self, kernel_connection: TestKernelConnection):
        # session:
        client = kernel_connection.km.client()

        msg = kernel_connection.km.session.msg("context_info_request", {})
        client.shell_channel.send(msg)

        response = None
        timeout = time.time() + 60
        while not response and time.time() < timeout:
            recv_msg = await client.get_iopub_msg(120)
            msg_type = recv_msg["header"]["msg_type"]
            if msg_type == "context_info_response":
                response = recv_msg

        assert response is not None
        content = response.get("content", None)
        assert "slug" in content
        assert "language" in content
        assert "info" in content

    async def test_msg_callbacks(self, kernel_connection: TestKernelConnection):

        client = kernel_connection.km.client()
        msg = kernel_connection.km.session.msg("context_info_request", {})

        # Delay sending of message slightly in case the response comes too quickly
        asyncio.get_event_loop().call_later(0.1, client.shell_channel.send, msg)
        msg = await kernel_connection.wait_on_msg("context_info_response")

        assert msg
        content = msg.get("content", None)

        assert "slug" in content
        assert "language" in content
        assert "info" in content
        assert kernel_connection.messages

    async def test_execute_request(self, kernel_connection: TestKernelConnection):
        result = await kernel_connection.execute_code("print('hello world')")
        assert result
        assert result["content"]["status"] == 'ok'
