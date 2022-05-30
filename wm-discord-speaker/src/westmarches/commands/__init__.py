from .agenda import AgendaCommands
from .chatbot import ChatbotCommands
from .forward import Forward
from .foundryvtt import FoundryCommands
from .inkarnate import InkarnateCommands
from .rumors import RumorsCommands
from ..utils import CompositeMetaClass


class Commands(RumorsCommands,
               ChatbotCommands,
               FoundryCommands,
               InkarnateCommands,
               AgendaCommands,
               Forward,
               metaclass=CompositeMetaClass):
    pass
