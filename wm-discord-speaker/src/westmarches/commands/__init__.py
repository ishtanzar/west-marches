from .agenda import AgendaCommands
from .chatbot import ChatbotCommands
from .forward import Forward
from .foundryvtt import FoundryCommands
from .inkarnate import InkarnateCommands
from .kanka import KankaCommands
from .rumors import RumorsCommands
from ..utils import CompositeMetaClass


class Commands(RumorsCommands,
               # ChatbotCommands,
               FoundryCommands,
               InkarnateCommands,
               KankaCommands,
               AgendaCommands,
               Forward,
               metaclass=CompositeMetaClass):
    pass
