"""Shared fixtures and helpers for the beaker_notebook secrets test suite.

Provides a fully-controllable concrete secret (``FakeSecret`` / ``make_secret``)
and helpers for building and inspecting signed multipart Jupyter messages.
"""

import json
from dataclasses import dataclass
from types import SimpleNamespace

from beaker_notebook.lib.jupyter_kernel_proxy import JupyterMessage
from beaker_notebook.lib.secrets.policies import Allow
from beaker_notebook.lib.secrets.secret_types import BaseSecret, PolicyRef


# -- secrets --


@dataclass(kw_only=True)
class FakeSecret(BaseSecret):
    """A concrete secret with fully-controllable policies and value for tests."""
    type = "fake-secret"

    subkernel_message_policy: PolicyRef = Allow
    ui_message_policy: PolicyRef = Allow
    agent_message_policy: PolicyRef = Allow
    beaker_kernel_environment_policy: PolicyRef = Allow
    subkernel_environment_policy: PolicyRef = Allow

    name: str = "SECRET_KEY"
    source_value: str = "s3cr3t-value"
    break_get_value: bool = False

    def get_value(self):
        if self.break_get_value:
            # Simulates a server-bound secret (app trait, config provider) whose
            # resolution cannot run in the kernel runtime -- only the injected
            # _value is usable there.
            raise RuntimeError("resolution unavailable in kernel runtime")
        return self.source_value


def make_secret(
    value="s3cr3t",
    *,
    subkernel=Allow,
    ui=Allow,
    agent=Allow,
    name="SECRET_KEY",
    set_value=True,
    break_get_value=False,
) -> FakeSecret:
    secret = FakeSecret(
        subkernel_message_policy=subkernel,
        ui_message_policy=ui,
        agent_message_policy=agent,
        beaker_kernel_environment_policy=Allow,
        subkernel_environment_policy=Allow,
        name=name,
        source_value=value,
        break_get_value=break_get_value,
    )
    if set_value:
        # Mirror the kernel-side path where the resolved value is injected
        # directly (BaseSecret.from_dict) rather than looked up locally.
        secret._value = value
    return secret


# -- multipart messages --


def signed_parts(content, *, key=b"testkey", identities=(b"id",), buffers=()):
    """Build a signed multipart message (list of byte frames) carrying `content`."""
    header = {"msg_id": "m1", "msg_type": "execute_result", "session": "sess"}
    parent = {"msg_id": "p1"}
    metadata = {}
    raw = (
        list(identities)
        + [
            JupyterMessage.DELIMITER,
            b"placeholder-signature",
            json.dumps(header).encode(),
            json.dumps(parent).encode(),
            json.dumps(metadata).encode(),
            json.dumps(content).encode(),
        ]
        + list(buffers)
    )
    return JupyterMessage.parse(raw).sign_using(key).parts


async def run_redact_secrets(secrets, destination, parts):
    """Drive the real ``BeakerKernel.redact_secrets`` flow with lightweight fakes.

    Exercises the actual scrubbing path (parse -> sanitize decoded fields ->
    reserialize) rather than calling a policy on raw frames directly, so tests
    reflect what the kernel really does on the wire. ``destination`` is what the
    proxy's ``get_destination`` would return ("client" or "subkernel").
    """
    from beaker_notebook.kernel import BeakerKernel

    fake_self = SimpleNamespace(secrets=list(secrets))
    fake_server = SimpleNamespace(get_destination=lambda _stream: destination)
    return await BeakerKernel.redact_secrets(fake_self, fake_server, target_stream=None, data=parts)


def wire_bytes(parts) -> bytes:
    return b"".join(parts)


def _iter_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            yield from _iter_strings(key)
            yield from _iter_strings(value)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            yield from _iter_strings(value)


def decoded_strings(parts) -> list[str]:
    """Every decoded (unescaped) string leaf in the message fields.

    Checking membership against these -- not a re-serialized JSON blob, which
    would re-escape the secret and hide a leak -- is what catches a secret that
    survived scrubbing inside a JSON-escaped payload.
    """
    msg = JupyterMessage.parse(parts)
    fields = [msg.header, msg.parent_header, msg.metadata, msg.content]
    return list(_iter_strings(fields))
