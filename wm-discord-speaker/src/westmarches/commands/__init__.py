from .agenda import AgendaCommands
from .chatbot import ChatbotCommands
from .foundryvtt import FoundryCommands
from .rumors import RumorsCommands
from ..utils import CompositeMetaClass


class Commands(RumorsCommands,
               ChatbotCommands,
               FoundryCommands,
               AgendaCommands,
               metaclass=CompositeMetaClass):
    pass
