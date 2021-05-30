from .chatbot import ChatbotCommands
from .foundryvtt import FoundryCommands
from .rumors import RumorsCommands
from ..utils import CompositeMetaClass


class Commands(RumorsCommands,
               ChatbotCommands,
               FoundryCommands,
               metaclass=CompositeMetaClass):
    pass
