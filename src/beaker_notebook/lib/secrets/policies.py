import asyncio
import copy
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, MutableSequence, MutableMapping, Literal, TypeAlias, TypeVar

from beaker_notebook.lib.secrets.validations import Validation, not_in


if TYPE_CHECKING:
    from beaker_notebook.lib.secrets.secret_types import BaseSecret


PolicyTypes: TypeAlias = Literal["redact", "remove", "last4", "allow"]

MappedContent = TypeVar("MappedContent", bound=MutableMapping)
SequencedContent = TypeVar("SequencedContent", bound=MutableSequence)

key_regex = re.compile(r'__([^:]+):([0-9#]+)__')
def next_key(key: str, mapping: MutableMapping):
    match = key_regex.search(key)
    if not match:
        return '?'
    cls_name = match.group(1)
    count = len([k for k in mapping.keys() if (m := key_regex.search(k)) and m.group(1) == cls_name])
    num = count
    while (new_key := key_regex.sub(lambda m: f"__{m.group(1)}:{num}__", key)) in mapping:
        num += 1
    return new_key

@dataclass
class BasePolicy:
    type: PolicyTypes
    validations: MutableSequence[Validation] = field(default_factory=lambda: [not_in,])

    async def replacement(self, secret_str: str):
        raise NotImplementedError(f"Policy '{BasePolicy}' does not define a sanitize function")

    def _sanitize_func_for(self, target: Any):
        match target:
            case str():
                return self._sanitize_str
            case {**mapping}:
                return self._sanitize_mapping
            case [*list]:
                return self._sanitize_list
            case bytes():
                return self._sanitize_bytes
            case _:
                return None

    async def _sanitize_bytes(self, secret: "BaseSecret", content: bytes) -> bytes:
        secret_str = secret.value
        if secret_str is None:
            return content
        secret_bytes = secret_str.encode()
        replacement: str = await self.replacement(secret_str)
        replacement_bytes = replacement.encode()
        sanitized = content.replace(secret_bytes, replacement_bytes)

        await asyncio.gather(*[
            validation_func(secret_bytes, sanitized) for validation_func in self.validations
        ])

        return sanitized


    async def _sanitize_str(self, secret: "BaseSecret", content: str) -> str:
        secret_str = secret.value
        if secret_str is None:
            return content
        replacement = await self.replacement(secret_str)
        sanitized = content.replace(secret_str, replacement)

        await asyncio.gather(*[
            validation_func(secret_str, sanitized) for validation_func in self.validations
        ])

        return sanitized

    async def _sanitize_list(self, secret: "BaseSecret", content: SequencedContent) -> SequencedContent:
        # Walk a list, sanitizing each item
        for idx, value in enumerate(content):
            sanitize_func = self._sanitize_func_for(value)
            if sanitize_func is None:
                continue
            content[idx] = await sanitize_func(secret, value)
        return content

    async def _sanitize_mapping(self, secret: "BaseSecret", content: MappedContent) -> MappedContent:
        # Walk dict, looking for strings and do a sanitization on each string
        to_remap: list[tuple[str, str]] = []
        key_policy = MappingKey()
        for key, value in content.items():
            key_sanitize_func = key_policy._sanitize_func_for(key)
            value_sanitize_func = self._sanitize_func_for(value)
            if key_sanitize_func:
                new_key = await key_sanitize_func(secret, key)
                if new_key != key:
                    to_remap.append((key, new_key))
            if value_sanitize_func:
                content[key] = await value_sanitize_func(secret, value)

        # Remap after walking to avoid mutating keys during iteration
        for key, new_key in to_remap:
            new_key = next_key(new_key, content)
            content[new_key] = content.pop(key)
        return content

    async def sanitize(self, secret: "BaseSecret", content: str|dict|list|bytes):
        sanitize_func = self._sanitize_func_for(content)
        if sanitize_func is None:
            return content
        target = copy.deepcopy(content)
        return await sanitize_func(secret, target)

@dataclass
class Allow(BasePolicy):
    """
    This policy does not modify the content in any way.
    Only for use in high-trust situations or debugging
    """

    type: PolicyTypes = "allow"

    # TODO: Add warning on initialization about this being insecure?

    async def sanitize(self, secret, content):
        return content


@dataclass
class Redact(BasePolicy):
    type: PolicyTypes = "redact"

    async def replacement(self, secret_str):
        return "#" * len(secret_str)


@dataclass
class Remove(BasePolicy):
    type: PolicyTypes = "remove"

    async def replacement(self, secret_str):
        return ""


@dataclass
class Last4(BasePolicy):
    type: PolicyTypes = "last4"

    async def replacement(self, secret_str):
        secret_len = len(secret_str)
        if secret_len < 6:
            # Returning last four chars could is too much information for such a short secret.
            return "####"
        hash = "#" * (secret_len - 4)
        return f"{hash}{secret_str[-4:]}"


@dataclass
class MappingKey(BasePolicy):
    type: PolicyTypes = "mapping-key"

    def _secret_value_str(self, secret: "BaseSecret"):
        secret_str = secret.type.upper()
        return f"__{secret_str}:#__"

    async def _sanitize_bytes(self, secret: "BaseSecret", content: bytes) -> bytes:
        secret_str = secret.value
        if secret_str is None:
            return content
        secret_bytes = secret_str.encode()
        replacement: str = self._secret_value_str(secret)
        replacement_bytes = replacement.encode()
        sanitized = content.replace(secret_bytes, replacement_bytes)

        await asyncio.gather(*[
            validation_func(secret_bytes, sanitized) for validation_func in self.validations
        ])

        return sanitized

    async def _sanitize_str(self, secret: "BaseSecret", content: str) -> str:
        secret_str = secret.value
        if secret_str is None:
            return content
        replacement = self._secret_value_str(secret)
        sanitized = content.replace(secret_str, replacement)

        await asyncio.gather(*[
            validation_func(secret_str, sanitized) for validation_func in self.validations
        ])

        return sanitized

