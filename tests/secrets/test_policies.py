"""
Tests for beaker_notebook.lib.secrets policy engine and secret (de)serialization.

Covers the *correct* behavior of the sanitization policies independent of the
wire/message plumbing (see test_secrets_message_scrubbing.py for that path):

- Allow leaves content untouched
- Redact replaces the secret with equal-length masking across str/bytes/list/dict
- Redact preserves surrounding structure (nested dicts/lists are not dropped)
- Remove eliminates the secret value from str / bytes-frame list / dict content
- Last4 reveals at most the trailing four characters, never the prefix
- not_in validation raises iff the secret survives
- BaseSecret.value falls back to get_value() when no explicit value was injected
- to_dict / from_dict round-trips the class, per-channel policies, and value

Several assertions encode behavior the current implementation does not yet
satisfy (Remove over a frame list, nested-dict preservation, Last4 masking,
the .value fallback); those are deliberate and describe the target behavior.
"""

import json

import pytest

from beaker_notebook.lib.secrets.policies import Allow, Redact, Remove, Last4
from beaker_notebook.lib.secrets.secret_types import BaseSecret, SystemEnvironmentSecret
from beaker_notebook.lib.secrets.validations import not_in, SecretValidationError

from tests.secrets.util import make_secret


# -- Allow --


async def test_allow_leaves_string_untouched():
    secret = make_secret("s3cr3t")
    assert await Allow().sanitize(secret, "token=s3cr3t;") == "token=s3cr3t;"


async def test_allow_leaves_container_untouched():
    secret = make_secret("s3cr3t")
    payload = {"a": ["s3cr3t"], "b": {"c": "s3cr3t"}}
    assert await Allow().sanitize(secret, payload) == payload


# -- Redact --


async def test_redact_string_masks_equal_length():
    secret = make_secret("s3cr3t")
    out = await Redact().sanitize(secret, "token=s3cr3t;")
    assert out == "token=######;"
    assert "s3cr3t" not in out


async def test_redact_bytes():
    secret = make_secret("s3cr3t")
    out = await Redact().sanitize(secret, b"key=s3cr3t")
    assert out == b"key=######"


async def test_redact_nested_dict_preserves_structure():
    secret = make_secret("s3cr3t")
    out = await Redact().sanitize(
        secret, {"outer": {"inner": "x s3cr3t"}, "keep": "ok"}
    )
    # The dict (and its nested dict) must survive as a dict, not be dropped/nulled.
    assert isinstance(out, dict)
    assert out["keep"] == "ok"
    assert isinstance(out["outer"], dict)
    assert "s3cr3t" not in json.dumps(out)


async def test_redact_list_preserves_elements():
    secret = make_secret("s3cr3t")
    out = await Redact().sanitize(secret, ["x s3cr3t", {"k": "s3cr3t"}])
    assert out[0] == "x ######"
    assert out[1] == {"k": "######"}


# -- Remove --


async def test_remove_string_eliminates_secret():
    secret = make_secret("s3cr3t")
    out = await Remove().sanitize(secret, "a s3cr3t b")
    assert "s3cr3t" not in out


async def test_remove_bytes_frame_list_eliminates_secret():
    """Remove applied to a multipart-style list of byte frames (the wire case)
    must eliminate the secret from every frame."""
    secret = make_secret("s3cr3t")
    frames = [b'{"code":"key=s3cr3t"}', b"<IDS|MSG>"]
    out = await Remove().sanitize(secret, frames)
    assert all(b"s3cr3t" not in frame for frame in out)


async def test_remove_dict_eliminates_secret_value():
    secret = make_secret("s3cr3t")
    out = await Remove().sanitize(secret, {"code": "key=s3cr3t"})
    assert isinstance(out, dict)
    assert "s3cr3t" not in json.dumps(out)


# -- Last4 --


async def test_last4_reveals_only_trailing_four():
    secret = make_secret("abcdefghij")  # length 10
    out = await Last4().sanitize(secret, "abcdefghij")
    assert "abcdefghij" not in out
    # Only the final four characters may be revealed; the prefix must not leak.
    assert out.endswith("ghij")
    assert "abcdef" not in out
    assert out == "######ghij"


async def test_last4_short_secret_fully_masked():
    secret = make_secret("abcd")  # length < 6
    out = await Last4().sanitize(secret, "abcd")
    assert out == "####"


# -- validations --


async def test_not_in_raises_when_secret_survives():
    with pytest.raises(SecretValidationError):
        await not_in("s3cr3t", "leftover s3cr3t here")


async def test_not_in_passes_when_absent():
    await not_in("s3cr3t", "nothing sensitive here")


# -- value property --


async def test_value_falls_back_to_get_value():
    """A secret constructed without an injected value must resolve via get_value()."""
    secret = make_secret("resolved-val", set_value=False)
    assert secret.value == "resolved-val"


# -- serialization round-trip --


def test_to_dict_from_dict_round_trip(monkeypatch):
    monkeypatch.setenv("MY_TOKEN", "abc123")
    secret = SystemEnvironmentSecret(name="MY_TOKEN")

    data = secret.to_dict(with_value=True)
    assert data["_value"] == "abc123"

    restored = BaseSecret.from_dict(dict(data))
    assert isinstance(restored, SystemEnvironmentSecret)
    assert restored.name == "MY_TOKEN"
    assert restored.value == "abc123"
    # Per-channel policies survive as instantiated policy objects.
    assert isinstance(restored.subkernel_message_policy, Redact)
    assert isinstance(restored.ui_message_policy, Redact)


# -- misc

async def test_dict_key_scrubbed():
    secret1 = make_secret("s3cr3t")
    secret2 = make_secret("0th3r")
    payload = {
        "token": "s3cr3t;",
        "s3cr3t": "abc",
        "my-s3cr3t": "def",
        "0th3r": "ghi",
        "my-0th3r": "jkl",
    }
    out1 = await Remove().sanitize(secret1, payload)
    out2 = await Remove().sanitize(secret2, out1)

    assert "s3cr3t" not in out2
    assert out2 == {
        "token": ";",
        "__FAKE-SECRET:0__": "abc",
        "my-__FAKE-SECRET:1__": "def",
        "__FAKE-SECRET:2__": "ghi",
        "my-__FAKE-SECRET:3__": "jkl",
    }
