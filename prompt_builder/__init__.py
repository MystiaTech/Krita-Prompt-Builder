from krita import Krita, Extension, DockWidget, DockWidgetFactory, DockWidgetFactoryBase
from .prompt_builder import PromptBuilderDocker


class PromptBuilderExtension(Extension):
    """Extension wrapper that registers the Prompt Builder docker when Krita is ready."""

    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        """Called when Krita is fully initialized. Register the docker here."""
        Krita.instance().addDockWidgetFactory(
            DockWidgetFactory(
                "prompt_builder",
                DockWidgetFactoryBase.DockRight,
                PromptBuilderDocker
            )
        )

    def createActions(self, window):
        pass


# Register the extension — Krita will call setup() when ready
Krita.instance().addExtension(PromptBuilderExtension(Krita.instance()))
