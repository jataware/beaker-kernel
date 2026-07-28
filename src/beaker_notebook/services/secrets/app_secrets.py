import inspect
import weakref
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, TypeGuard

from traitlets import HasTraits
from traitlets.config import Application, Configurable, SingletonConfigurable, LoggingConfigurable

from beaker_notebook.services.auth import BeakerUser
from beaker_notebook.lib.secrets.policies import Allow, Redact, Remove
from beaker_notebook.lib.secrets.secret_types import BaseSecret, PolicyRef

if TYPE_CHECKING:
    pass


@dataclass(kw_only=True)
class AppTraitSecret(BaseSecret):
    type: str = "app-trait-secret"
    subkernel_message_policy: PolicyRef = Remove
    ui_message_policy: PolicyRef = Redact
    agent_message_policy: PolicyRef = Redact
    beaker_kernel_environment_policy: PolicyRef = Allow
    subkernel_environment_policy: PolicyRef = Remove

    _index: ClassVar[dict[str, Configurable]] = {}
    config_str: str

    def _update_index(self):
        # Fetch the global singleton of the app instance
        app = Application.instance()
        seen, queue = set(), [app]
        while queue:
            obj = queue.pop()
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            for klass in type(obj).__mro__:
                if klass in (LoggingConfigurable, Configurable, SingletonConfigurable):
                    break
                self._index.setdefault(klass.__name__, obj)
            for _, value in inspect.getmembers_static(obj, lambda member: isinstance(member, Configurable)):
                if isinstance(value, HasTraits):
                    queue.append(value)
                elif isinstance(value, (list, tuple, dict)):
                    queue.extend(v for v in (value.values() if isinstance(value, dict) else value)
                                if isinstance(v, HasTraits))

    def __post_init__(self, configurable=None):
        if configurable is not None:
            self._configurable_ref = weakref.ref(configurable)
        super().__post_init__()

    def get_value(self):
        configurable_name, trait_name = self.config_str.split(".", maxsplit=1)
        if configurable_name not in self._index:
            self._update_index()
        configurable = self._index.get(configurable_name, None)
        if configurable is None:
            raise ValueError(f"<{self.__class__.__name__}: name='{self.config_str}'> is not available as '{configurable_name}' cannot be located.")
        return getattr(configurable, trait_name, None)


def is_app_trait_secret(secret: BaseSecret) -> TypeGuard[AppTraitSecret]:
    return isinstance(secret, AppTraitSecret)