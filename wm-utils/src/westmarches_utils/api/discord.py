from dataclasses import dataclass


@dataclass
class DiscordUser:
    id: int
    name: str
    discriminator: str


@dataclass
class DiscordMessage:
    id: int
    content: str
    author: DiscordUser
    created_at: float
