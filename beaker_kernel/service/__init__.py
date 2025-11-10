import importlib
import sys
import types
import typing

refactor_map = {
    'beaker_kernel.service.admin_utils': {
        'build_edges_map': 'beaker_kernel.lib.admin',
        'build_proc_info': 'beaker_kernel.lib.admin',
        'fetch_kernel_info': 'beaker_kernel.lib.admin',
        'fetch_system_stats': 'beaker_kernel.lib.admin',
    },
    'beaker_kernel.service.api': {},
    'beaker_kernel.service.api.handlers': {
        'add_handler_prefix': 'beaker_kernel.app.api.handlers',
        'find_api_handlers': 'beaker_kernel.app.api.handlers',
        'register_api_handlers': 'beaker_kernel.app.api.handlers',
    },
    'beaker_kernel.service.api.integrations': {
        'BeakerAPIMixin': 'beaker_kernel.app.api.integrations',
        'IntegrationHandler': 'beaker_kernel.app.api.integrations',
        'IntegrationResourceHandler': 'beaker_kernel.app.api.integrations',
        'get_context': 'beaker_kernel.app.api.integrations',
    },
    'beaker_kernel.service.api.notebook': {
        'NotebookHandler': 'beaker_kernel.app.api.notebook'
    },
    'beaker_kernel.service.auth': {
        'BeakerUser': 'beaker_kernel.services.auth',
        'current_request': 'beaker_kernel.services.auth',
        'current_user': 'beaker_kernel.services.auth',
        'BeakerAuthorizer': 'beaker_kernel.services.auth',
        'BeakerIdentityProvider': 'beaker_kernel.services.auth',
        'BeakerUser': 'beaker_kernel.services.auth',
        'BeakerPermission': 'beaker_kernel.services.auth',
        'BeakerRole': 'beaker_kernel.services.auth',
        'RoleBasedUser': 'beaker_kernel.services.auth',
    },
    'beaker_kernel.service.auth.dummy': {
        'DummyAuthorizer': 'beaker_kernel.services.auth.dummy',
        'DummyIdentityProvider': 'beaker_kernel.services.auth.dummy',
    },
    'beaker_kernel.service.auth.notebook': {
        'NotebookAuthorizer': 'beaker_kernel.services.auth.notebook',
        'NotebookIdentityProvider': 'beaker_kernel.services.auth.notebook',
    },
    'beaker_kernel.service.base': {
        'BaseBeakerApp': 'beaker_kernel.app.base',
        'BeakerKernelManager': 'beaker_kernel.services.kernel.manager',
        'BeakerKernelMappingManager': 'beaker_kernel.services.kernel.manager',
        'BeakerKernelSpecManager': 'beaker_kernel.services.kernel.spec',
        'BeakerSessionManager': 'beaker_kernel.services.session',
    },
    'beaker_kernel.service.dev': {
        'BeakerWatchDog': 'beaker_kernel.app.dev_app',
        'DevBeakerJupyterApp': 'beaker_kernel.app.dev_app',
        'create_observer': 'beaker_kernel.app.dev_app',
    },
    'beaker_kernel.service.handlers': {
        'ConfigController': 'beaker_kernel.app.handlers',
        'ConfigHandler': 'beaker_kernel.app.handlers',
        'ContextHandler': 'beaker_kernel.app.handlers',
        'DownloadHandler': 'beaker_kernel.app.handlers',
        'ExportAsHandler': 'beaker_kernel.app.handlers',
        'PageHandler': 'beaker_kernel.app.handlers',
        'StatsHandler': 'beaker_kernel.app.handlers',
        'register_handlers': 'beaker_kernel.app.handlers',
        'request_log_handler': 'beaker_kernel.app.handlers',
        'sanitize_env': 'beaker_kernel.app.handlers',
    },
    'beaker_kernel.service.multiuser': {
        'BeakerMultiuserApp': ('beaker_kernel.app.multiuser_app', 'BeakerMultiUserServerApp'),
        'BeakerMultiUserServerApp': 'beaker_kernel.app.multiuser_app',
    },
    'beaker_kernel.service.notebook': {'BeakerNotebookApp': 'beaker_kernel.app.notebook_app'},
    'beaker_kernel.service.server': {'BeakerServerApp': 'beaker_kernel.app.server_app'},
    'beaker_kernel.service.storage': {},
    'beaker_kernel.service.storage.base': {
        'BaseBeakerContentsManager': 'beaker_kernel.services.storage.base',
        'BeakerLocalContentsHandler': 'beaker_kernel.services.storage.base',
        'BeakerLocalContentsManager': 'beaker_kernel.services.storage.base',
        'BeakerStorageManager': 'beaker_kernel.services.storage.base',
        'with_hidden_files': 'beaker_kernel.services.storage.base',
    },
    'beaker_kernel.service.storage.notebook': {
        'BaseNotebookManager': 'beaker_kernel.services.storage.notebook',
        'BrowserLocalDataNotebookManager': 'beaker_kernel.services.storage.notebook',
        'FileNotebookManager': 'beaker_kernel.services.storage.notebook',
        'NotebookInfo': 'beaker_kernel.services.storage.notebook',
        'with_hidden_files': 'beaker_kernel.services.storage.notebook',
    },
}


def _mod_getattr(mod: types.ModuleType, member: str, default: typing.Any = None):
    """
    Custom getattr function that only loads the modules on demand.
    """
    orig_member = member
    new_mod_info = mod._members.get(member, ImportError)
    if new_mod_info is ImportError:
        raise AttributeError()
    if isinstance(new_mod_info, str):
        new_mod_str = new_mod_info
    elif isinstance(new_mod_info, tuple):
        new_mod_str, member = new_mod_info
    new_mod = importlib.import_module(new_mod_str)
    result = getattr(new_mod, member, default)
    if result and result is not default:
        import warnings
        warnings.warn(
            f"Item '{orig_member} has moved from module '{mod.__name__}' to module '{new_mod_str}'. Please update your imports."
        )
    return result


# Register the old locations for each of the members so they can be imported
for mod_name, members in refactor_map.items():
    mod = types.ModuleType(mod_name)
    mod.__dict__["_members"] = members
    mod.__getattr__ = types.MethodType(_mod_getattr, mod)
    sys.modules[mod_name] = mod
