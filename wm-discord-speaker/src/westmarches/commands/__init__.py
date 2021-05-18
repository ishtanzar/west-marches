from .chatbot import ChatbotCommands
from .rumors import RumorsCommands
from ..utils import CompositeMetaClass


class Commands(RumorsCommands,
               ChatbotCommands,
               metaclass=CompositeMetaClass):
    pass
