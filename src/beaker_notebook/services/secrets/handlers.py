import typing

from beaker_notebook.lib.secrets.secret_types import BaseSecret
from beaker_notebook.services.secrets.app_secrets import AppTraitSecret
from beaker_notebook.services import ServiceApi, ServiceApiHandler, HTTPError

if typing.TYPE_CHECKING:
    from .manager import BeakerSecretsManager


class SecretsApi(ServiceApi):
    prefix = r"secrets"

    class ContextInfo(ServiceApiHandler):
        pattern = r"(?P<session>[\w_-]+)?"

        @staticmethod
        def _valid_secret(secret: BaseSecret) -> bool:
            # TODO: Stub to be filled out once boundaries are more clear
            return True

        @property
        def secrets_manager(self) -> "BeakerSecretsManager":
            secrets_manager = getattr(self.serverapp, "secrets_manager", None)
            if secrets_manager is None:
                raise HTTPError(404, "Secrets manager not found")
            return secrets_manager

        async def get(self, session=None):
            from dataclasses import asdict
            user = self.current_user

            secrets = await self.secrets_manager.get_kernel_secrets_for_user(user)
            # First we filter to only secrets that might apply, then we filter those to secrets that have a
            # replaceable value. E.g. get rid of empty strings, Nones, etc.
            secret_dicts = [secret.to_dict(with_value=True) for secret in secrets if self._valid_secret(secret)]
            filtered_output = [secret_dict for secret_dict in secret_dicts if secret_dict.get("_value", None)]

            self.write(filtered_output)

