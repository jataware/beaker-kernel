import click
import inspect


@click.group(name="subkernel")
def subkernel():
    """
    Commands for creating a new subkernel.
    """
    pass


# @subkernel.command(name="new")
# def new_subkernel():
#     """
#     Create a new subkernel.
#     """
#     pass


@click.option(
    "--all", "-a", "all",
    type=bool,
    is_flag=True,
    default=False,
    help="Show all subkernels, not just ones that are available."
)
@subkernel.command(name="list")
def list_subkernels(all):
    """
    List installed subkernels.

    Unless specified via the -all flag, only available subkernels will be displayed.
    Usually the reason why a subkernel will not be available is that a required kernel has not been installed in your
    current environment.

    Information on which kernels/packages are required to run a kernel is usually found in the docsting for a subkernel,
    viewable when run with the -a flag.
    """
    from beaker_kernel.lib.subkernels import autodiscover_subkernels
    # Fetch installed jupyter subkernels
    from jupyter_client.kernelspec import KernelSpecManager
    ksm = KernelSpecManager()
    kernel_specs = ksm.get_all_specs()
    subkernels = {
        name: cls
        for name, cls in autodiscover_subkernels().items()
        if all or getattr(cls, 'KERNEL_NAME', 'undetermined') in kernel_specs
    }
    if subkernels:
        click.echo("Currently installed subkernels:\n")
        for subkernel_name, subkernel_cls in subkernels.items():
            autodiscovery_data = getattr(subkernel_cls, '_autodiscovery', None)
            subkernel_doc = getattr(subkernel_cls, '__doc__', None)
            display_name = getattr(subkernel_cls, 'DISPLAY_NAME', subkernel_name.capitalize())
            kernel_name = getattr(subkernel_cls, 'KERNEL_NAME', 'undetermined') or 'undetermined'
            indent = 4
            output = [
                f"  {subkernel_name}{' ({})'.format(display_name)}:",
            ]
            if subkernel_doc:
                output.append(
                    f"{' ' * indent}'''" +
                    '\n'.join(
                        [
                            (
                                (' ' * indent) +
                                line
                            ) for line in subkernel_doc.splitlines()]
                    ) +
                    f"\n{' ' * indent}'''"
                )
            else:
                output.append(f"{' ' * indent}''' ( docstring not defined ) '''")
            output.extend([
                f"    Subkernel Class:           {subkernel_cls.__module__}.{subkernel_cls.__name__}",
                f"                                 ({inspect.getfile(subkernel_cls)})",
                f"    Display name:              {display_name}",
                f"    Jupyter kernel name:       {kernel_name}",
                f"    Jupyter kernel installed?: {str(kernel_name in kernel_specs).upper()}",
            ])
            if autodiscovery_data:
                output.append(
                    f"    Registration file:         {autodiscovery_data.get('mapping_file', 'unknown')}",
                )
            output.append("\n")
            click.echo("\n".join(output))
            click.echo("-" * 80)
    else:
        click.echo("No subkernels were found. Please check that you are running in the correct environment.")
    pass
