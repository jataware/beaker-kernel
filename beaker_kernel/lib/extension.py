import inspect
from typing import ClassVar

import click

class BeakerExtension:
    slug: str
    settings: "BeakerExtensionSettings"
    keybindings: "BeakerExtensionKeybindings"
    components: "BeakerExtensionComponents"

    def initialize(self):
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass


class BeakerExtensionSettings:
    pass

class BeakerExtensionKeybindings:
    pass

class BeakerExtensionComponents:
    pass

class BeakerCLICommands(click.Group):
    slug: ClassVar[str]
    group_description: ClassVar[str] = """Commands from extension"""

    @classmethod
    def as_group(cls):

        @click.group(cls=cls)
        def commands():
            pass
        commands.help = cls.group_description

        functions = inspect.getmembers(
            cls,
            lambda member: isinstance(member, click.Command)
        )
        for name, command in functions:
            commands.add_command(command, name=name)

        return commands
