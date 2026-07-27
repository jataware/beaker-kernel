"""
Tests for secret scrubbing over the wire (multipart Jupyter messages).

These drive the real ``BeakerKernel.redact_secrets`` flow (via ``run_redact_secrets``):
parse the multipart message, sanitize the decoded payload fields, reserialize.
They assert the security invariants a scrubbed message must uphold:

- The secret value never appears anywhere on the wire after scrubbing
- The message remains a structurally valid, re-parseable Jupyter message
- Per-channel policy selection is honored by destination (client vs subkernel)
- Secrets containing JSON-escaped characters (quotes/backslashes/non-ascii)
  are still scrubbed from the decoded content
- Binary buffers are passed through untouched and never raise on decode
"""

from beaker_notebook.lib.jupyter_kernel_proxy import JupyterMessage
from beaker_notebook.lib.secrets.policies import Allow, Redact, Remove

from tests.secrets.util import (
    make_secret,
    run_redact_secrets,
    signed_parts,
    wire_bytes,
    decoded_strings,
)


# -- redact over the wire --


async def test_redact_scrubs_secret_and_keeps_message_valid():
    secret = make_secret("s3cr3t", subkernel=Redact)
    parts = signed_parts({"data": {"text/plain": "k=s3cr3t"}})

    out = await run_redact_secrets([secret], "subkernel", parts)

    assert b"s3cr3t" not in wire_bytes(out)
    # Message is still structurally valid and can be re-parsed / re-signed.
    reparsed = JupyterMessage.parse(out)
    assert reparsed.content["data"]["text/plain"] == "k=######"


# -- remove over the wire --


async def test_remove_scrubs_secret_from_message():
    secret = make_secret("s3cr3t", subkernel=Remove)
    parts = signed_parts({"data": {"text/plain": "k=s3cr3t"}})

    out = await run_redact_secrets([secret], "subkernel", parts)

    assert b"s3cr3t" not in wire_bytes(out)


async def test_remove_uses_injected_value_not_get_value():
    """On the kernel side a secret carries an injected value and its server-bound
    get_value() may be unavailable; Remove must scrub via the injected value."""
    secret = make_secret("s3cr3t", subkernel=Remove, break_get_value=True)
    parts = signed_parts({"data": {"text/plain": "k=s3cr3t"}})

    out = await run_redact_secrets([secret], "subkernel", parts)

    assert b"s3cr3t" not in wire_bytes(out)


# -- per-channel policy selection --


async def test_channel_policies_are_independent():
    # Allow to the UI, Redact to the subkernel.
    secret = make_secret("s3cr3t", ui=Allow, subkernel=Redact)
    parts = signed_parts({"data": {"text/plain": "k=s3cr3t"}})

    ui_out = await run_redact_secrets([secret], "client", parts)
    sub_out = await run_redact_secrets([secret], "subkernel", parts)

    assert b"s3cr3t" in wire_bytes(ui_out)
    assert b"s3cr3t" not in wire_bytes(sub_out)


# -- secrets with JSON-escaped characters --


async def test_scrubs_secret_with_json_special_characters():
    secret_value = 'p@ss"w\\ordé'  # contains a quote, a backslash, and non-ascii
    secret = make_secret(secret_value, subkernel=Redact)
    parts = signed_parts({"data": {"text/plain": f"token={secret_value}"}})

    out = await run_redact_secrets([secret], "subkernel", parts)

    # Must remain a valid message (a naive byte-replace can corrupt the JSON)...
    reparsed = JupyterMessage.parse(out)
    assert reparsed.header["msg_type"] == "execute_result"
    # ...and the secret must not survive in any decoded string field.
    leaked = [s for s in decoded_strings(out) if secret_value in s]
    assert not leaked, f"secret leaked in decoded content: {leaked}"


# -- binary buffers --


async def test_binary_buffers_are_preserved_and_do_not_crash():
    secret = make_secret("s3cr3t", subkernel=Redact)
    blob = b"\x89PNG\r\n\x1a\n\xff\xfe\x00binary"  # not valid utf-8
    parts = signed_parts({"data": {"text/plain": "k=s3cr3t"}}, buffers=(blob,))

    out = await run_redact_secrets([secret], "subkernel", parts)

    assert blob in out  # buffer survives untouched
    assert b"s3cr3t" not in wire_bytes(out)
