import logging
from functools import lru_cache
from traitlets import Unicode, Bool

from jupyter_server.auth.identity import User, PasswordIdentityProvider
from jupyter_server.auth.authorizer import AllowAllAuthorizer

from . import BeakerAuthorizer, BeakerIdentityProvider, RoleBasedUser, current_request, current_user



class NotebookIdentityProvider(BeakerIdentityProvider, PasswordIdentityProvider):
    pass


class NotebookAuthorizer(BeakerAuthorizer, AllowAllAuthorizer):
    pass


authorizer = NotebookAuthorizer
identity_provider = NotebookIdentityProvider
