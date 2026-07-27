import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, Optional, TypeAlias, Type, TypeGuard, get_origin

# from beaker_notebook.services.auth import BeakerUser
from beaker_notebook.lib.secrets.policies import BasePolicy, Allow, Redact, Remove
from beaker_notebook.lib.utils import to_import_string, import_dotted_class

if TYPE_CHECKING:
    pass


PolicyRef: TypeAlias = BasePolicy | Type[BasePolicy]


@dataclass(kw_only=True)
class BaseSecret:
    type: ClassVar[str] = "base-secret"
    _value: Optional[str] = field(init=False, repr=False, hash=False, compare=False)

    subkernel_message_policy: PolicyRef
    ui_message_policy: PolicyRef
    agent_message_policy: PolicyRef
    beaker_kernel_environment_policy: PolicyRef
    subkernel_environment_policy: PolicyRef

    def __post_init__(self, *args, **kwargs):
        # Allows defining policies as a class or an instance
        # If the policy is a class, instantiate it as part of init
        for name, field_info in self.__dataclass_fields__.items():
            if field_info.type == PolicyRef:
                value = getattr(self, name)
                setattr(self, name, value())
        self._value = None

    def to_dict(self, with_value: bool = False):
        output = {
            "cls": to_import_string(self)
        }
        for key, field_def in self.__dataclass_fields__.items():
            if get_origin(field_def.type) == ClassVar:
                continue
            if key == "_value":
                continue
            field = getattr(self, key)
            match key, field:
                case _, BasePolicy():
                    field = {
                        "import_str": to_import_string(field)
                    }
                case _, val if callable(val):
                    continue
                case _, _:
                    pass
            output[key] = field
            if with_value:
                try:
                    output["_value"] = self.get_value()
                except Exception:
                    pass
        return output

    @classmethod
    def from_dict(cls, data: dict):
        result_cls = data.pop("cls")
        result_cls = import_dotted_class(result_cls)
        secret_value = data.pop("_value", None)

        for key, value in data.items():
            if isinstance(value, dict) and (import_str := value.get("import_str")):
                data[key] = import_dotted_class(import_str)

        secret = result_cls(**data)
        secret._value = secret_value
        return secret

    @property
    def value(self) -> Optional[str]:
        if self._value is not None:
            return self._value
        else:
            return self.get_value()

    def get_value(self) -> Optional[str]:
        raise NotImplementedError()


@dataclass(kw_only=True)
class EnvironmentSecret(BaseSecret):
    type = "env-secret"
    agent_message_policy: PolicyRef = Redact
    subkernel_message_policy: PolicyRef = Redact
    ui_message_policy: PolicyRef = Redact

    name: str

    def get_value(self):
        return os.environ.get(self.name)


@dataclass(kw_only=True)
class SystemEnvironmentSecret(EnvironmentSecret):
    type = "system-env-secret"
    subkernel_message_policy: PolicyRef = Redact
    ui_message_policy: PolicyRef = Redact
    beaker_kernel_environment_policy: PolicyRef = Allow
    subkernel_environment_policy: PolicyRef = Remove

    def get_value(self):
        import os
        return os.environ.get(self.name)


@dataclass(kw_only=True)
class UserEnvironmentSecret(EnvironmentSecret):
    type = "user-env-secret"
    subkernel_message_policy: PolicyRef = Allow
    ui_message_policy: PolicyRef = Allow
    beaker_kernel_environment_policy: PolicyRef = Remove
    subkernel_environment_policy: PolicyRef = Allow

    # user: Optional[BeakerUser] = None

    def get_value(self):
        return "USER ENV VALUE"


@dataclass(kw_only=True)
class SkillSecret(BaseSecret):
    type: str = "skill-secret"
    skill_name: str
    name: str
    default_value: Optional[str]

    def get_value(self):
        return os.environ.get(self.name)


@dataclass(kw_only=True)
class BeakerConfigProviderSecret(BaseSecret):
    OVERRIDE_KEY: ClassVar[str] = "__OVERRIDE__"

    type: str = "config-provider-secret"
    subkernel_message_policy: PolicyRef = Remove
    ui_message_policy: PolicyRef = Redact
    agent_message_policy: PolicyRef = Redact
    beaker_kernel_environment_policy: PolicyRef = Allow
    subkernel_environment_policy: PolicyRef = Remove

    provider_name: str

    def get_value(self):
        from beaker_notebook.lib.config import config as beaker_config
        if self.provider_name == self.OVERRIDE_KEY:
            return beaker_config.llm_service_token
        else:
            return beaker_config.provider.get(self.provider_name, {}).get("api_key", None)


def is_env_secret(secret: BaseSecret) -> TypeGuard[EnvironmentSecret]:
    return isinstance(secret, EnvironmentSecret)


def is_system_env_secret(secret: BaseSecret) -> TypeGuard[SystemEnvironmentSecret]:
    return isinstance(secret, SystemEnvironmentSecret)


def is_user_env_secret(secret: BaseSecret) -> TypeGuard[UserEnvironmentSecret]:
    return isinstance(secret, UserEnvironmentSecret)
