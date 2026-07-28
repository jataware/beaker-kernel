import copy
import inspect
import os
from itertools import chain
from dataclasses import dataclass, is_dataclass, asdict
from typing import TYPE_CHECKING, Any, Collection, Literal, TypeAlias, Optional

import traitlets
from traitlets import Type, default, HasTraits
from traitlets.config.configurable import Configurable, LoggingConfigurable
from traitlets.utils.importstring import import_item

from beaker_notebook.lib.secrets.policies import PolicyTypes, BasePolicy, Allow, Redact, Remove
from beaker_notebook.lib.secrets.secret_types import (
    BaseSecret,  UserEnvironmentSecret, SystemEnvironmentSecret, BeakerConfigProviderSecret,
    is_env_secret, is_system_env_secret, is_user_env_secret
)
from beaker_notebook.services.secrets.app_secrets import AppTraitSecret


if TYPE_CHECKING:
    from beaker_notebook.app.base import BaseBeakerApp
    from beaker_notebook.lib.context import BeakerContext
    from beaker_notebook.services.auth import BeakerUser


def index_configurables(root):
    from traitlets.config import SingletonConfigurable, LoggingConfigurable, Configurable
    seen, index, queue = set(), {}, [root]
    while queue:
        obj = queue.pop()
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        for klass in type(obj).__mro__:
            if klass in (LoggingConfigurable, Configurable, SingletonConfigurable):
                break
            index.setdefault(klass.__name__, obj)
        for _, value in  inspect.getmembers(obj, lambda member: isinstance(obj, Configurable)):
            if isinstance(value, HasTraits):
                queue.append(value)
            elif isinstance(value, (list, tuple, dict)):
                queue.extend(v for v in (value.values() if isinstance(value, dict) else value)
                             if isinstance(v, HasTraits))
    return index


class BeakerSecretsManager(LoggingConfigurable):
    parent: "BaseBeakerApp"
    _secrets: list[BaseSecret]

    app_trait_secrets: list[str] = traitlets.List(
        trait=traitlets.Unicode,
        config=True,
        default_value=[
            "Application.cookie_secret",
            "IdentityProvider.token",
            "GatewayClient.auth_token",
        ]
    )
    extra_app_trait_secrets: list[str] = traitlets.List(
        trait=traitlets.Unicode,
        config=True,
        default_value=[],
    )

    extra_user_env_vars: list[str] = traitlets.List(
        trait=traitlets.Unicode,
        config=True,
        default_value=[],
    )
    extra_system_env_vars: list[str] = traitlets.List(
        trait=traitlets.Unicode,
        config=True,
        default_value=[],
    )

    env_key_detection_anywhere: list[str] = traitlets.Tuple(
        trait=traitlets.Unicode,
        config=True,
        default_value=(
           "secret",
           "private",
           "password",
           "passwd",
           "creds",
           "credentials",
           "token",
           "auth",
           "passphrase",
        ),
    )
    extra_env_key_detection_anywhere: list[str] = traitlets.Tuple(
        trait=traitlets.Unicode,
        config=True,
        default_value=tuple(),
    )
    env_key_detection_suffix: list[str] = traitlets.Tuple(
        trait=traitlets.Unicode,
        config=True,
        default_value=(
            "_key",
            "_key_id",
        ),
    )
    extra_env_key_detection_suffix: list[str] = traitlets.Tuple(
        trait=traitlets.Unicode,
        config=True,
        default_value=tuple(),
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._secrets = []
        from .handlers import SecretsApi
        # TODO: Defining handlers here is clunky, There should be a more elegant way.
        self.parent.handlers.extend(SecretsApi.handlers)

    def add_secret(self, secret: BaseSecret):
        if secret in self._secrets:
            return
        self._secrets.append(secret)

    def add_secrets(self, secrets: Collection[BaseSecret]):
        for secret in secrets:
            self.add_secret(secret)

    @property
    def secrets(self) -> list[BaseSecret]:
        return self._secrets

    async def sanitize_kernel_environment_vars(self, env: dict) -> dict[str, str]:
        result = copy.copy(env)
        for secret in self._secrets:
            policy = secret.beaker_kernel_environment_policy
            if is_env_secret(secret) and secret.name in result:
                if isinstance(policy, Allow):
                    continue
                elif isinstance(policy, Remove):
                    result.pop(secret.name)
                else:
                    result[secret.name] = await policy.sanitize(secret, result[secret.name])
        return result

    async def sanitize_subkernel_envionment_vars(self, user: "BeakerUser", env: dict) -> dict[str, str]:
        result = copy.copy(env)
        if user and user.secrets:
            self.add_secrets(user.secrets)
        for secret in self._secrets:
            policy = secret.subkernel_environment_policy
            if is_env_secret(secret) and secret.name in result:
                if isinstance(policy, Allow):
                    continue
                elif isinstance(policy, Remove):
                    result.pop(secret.name)
                else:
                    result[secret.name] = await policy.sanitize(secret, result[secret.name])
            if is_user_env_secret(secret) and secret.name not in result:
                # Add the user secret to the environment if it doesn't exist TODO: Determine if this is the right thing
                result[secret.name] = secret.value
        return result


    def _secret_env_vars(self) -> list[str]:
        sensitive_env_keys = set()
        # Ensure all keys are lowercase for matching
        suffix_keys = tuple(map(str.lower, self.env_key_detection_suffix + self.extra_env_key_detection_suffix))
        anywhere_keys = tuple(map(str.lower, self.env_key_detection_anywhere + self.extra_env_key_detection_anywhere))
        # Check each key for match
        for key in os.environ.keys():
            lkey = key.lower()
            if (
                lkey.endswith(suffix_keys) or
                any(substr in lkey for substr in anywhere_keys)
            ):
                sensitive_env_keys.add(key)
        return sorted(sensitive_env_keys)


    async def collect_system_secrets(self, app: "BaseBeakerApp") -> list[BaseSecret]:
        from beaker_notebook.lib.config import config as beaker_config

        # Environment secrets from configuration
        discovered_system_env_secrets = [SystemEnvironmentSecret(name=env_name) for env_name in self._secret_env_vars()]
        extra_system_envs = [SystemEnvironmentSecret(name=env_name) for env_name in self.extra_system_env_vars]
        extra_user_envs = [UserEnvironmentSecret(name=env_name) for env_name in self.extra_user_env_vars]

        # Secrets from server app traits/configuration
        app_trait_secrets = [AppTraitSecret(config_str=config_st) for config_st in self.app_trait_secrets + self.extra_app_trait_secrets]

        # LLM secrets from Beaker Config
        beaker_config_secrets = [
            BeakerConfigProviderSecret(provider_name=provider_name)
            for provider_name, provider_config in beaker_config.providers.items()
            if provider_config["api_key"]
        ]
        if beaker_config.llm_service_token:
            beaker_config_secrets.append(BeakerConfigProviderSecret(provider_name=BeakerConfigProviderSecret.OVERRIDE_KEY))

        system_secrets = list(chain(
            discovered_system_env_secrets,
            extra_system_envs,
            extra_user_envs,
            app_trait_secrets,
            beaker_config_secrets,
        ))

        return system_secrets


    async def get_kernel_secrets_for_user(self, user: "Optional[BeakerUser]"):
        # TODO: filter secrets and add in user's secrets if any
        # set to push = { secrets owned by this session's scope } ∩ { secrets with any non-Allow message policy }.
        return self.secrets
