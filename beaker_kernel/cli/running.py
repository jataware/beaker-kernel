import os
import subprocess
import sys

import click
import webbrowser

from .helpers import ensure_config


@click.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
@ensure_config
def notebook(ctx, extra_args):
    """
    Start Beaker in local mode and opens a notebook.
    """
    from beaker_kernel.server.main import BeakerJupyterApp
    app = None
    try:
        app = BeakerJupyterApp.initialize_server(argv=extra_args)
        app.start()
    except (InterruptedError, KeyboardInterrupt, EOFError) as err:
        print(err)
    finally:
        if app:
            app.stop()


@click.group(name="dev", invoke_without_command=True)
@click.option("--no-open-notebook", "-n", is_flag=True, default=False, type=bool, help="Prevent opening the notebook in a webbrowser.")
@click.pass_context
@ensure_config
def dev(ctx: click.Context, no_open_notebook):
    """
    Start Beaker server in development mode. (Subcommands available)
    """
    # Don't run if we are running watch
    if ctx.invoked_subcommand is None:
        # Invert the default behavior around opening the notebook as `watch` has an opposite default.
        ctx.params["open_notebook"] = not ctx.params.pop("no_open_notebook")
        # Invoke watch as default action
        ctx.forward(watch)
        return


@dev.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
@click.option("--open-notebook", "-n", is_flag=True, default=False, type=bool, help="Open a notebook in a webbrowser.")
def serve(open_notebook, extra_args):
    from beaker_kernel.server.dev import DevBeakerJupyterApp

    try:
        app = DevBeakerJupyterApp.initialize_server(argv=extra_args)
        if open_notebook:
            webbrowser.open(app.public_url)
        app.start()
    finally:
        app.stop()


@dev.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.option("--extra_dir", multiple=True)
@click.option("--open-notebook", "-n", is_flag=True, default=False, type=bool, help="Open a notebook in a webbrowser.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def watch(extra_dir=None, open_notebook=None, extra_args=None):
    from beaker_kernel.server.dev import create_observer
    app_subprocess = None
    extra_args = extra_args or []

    def restart():
        click.echo(" *** Restarting service *** \n")
        app_subprocess.terminate()

    observer = create_observer(extra_dir, restart)
    try:
        while True:
            try:
                args = [
                    sys.executable,
                    sys.argv[0], "dev", "serve", *extra_args
                ]
                if open_notebook:
                    args.append("--open-notebook")
                app_subprocess = subprocess.Popen(
                    args,
                    env=os.environ,
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                )
                app_subprocess.wait()
            except (InterruptedError, KeyboardInterrupt, EOFError) as err:
                click.echo("y")
                click.echo("Shutting down...")
                break
    finally:
        if app_subprocess:
            click.echo("Cleaning up...")
            app_subprocess.terminate()
        observer.unschedule_all()
        observer.stop()
        del observer
