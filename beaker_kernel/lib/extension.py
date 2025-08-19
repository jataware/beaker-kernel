
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
