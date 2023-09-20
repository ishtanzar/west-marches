from .chatbot import ChatbotCommands
from .forward import Forward
from .foundryvtt import FoundryCommands
from .inkarnate import InkarnateCommands
from .kanka import KankaCommands
from .management import ManagementCommands
from .rumors import RumorsCommands
from ..utils import CompositeMetaClass


class Commands(
    # RumorsCommands,
    # ChatbotCommands,
    FoundryCommands,
    InkarnateCommands,
    KankaCommands,
    Forward,
    ManagementCommands,
    metaclass=CompositeMetaClass
):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
