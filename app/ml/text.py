"""How an issue becomes one piece of text for the model.

Training and the running application both import this function. If they built
the text differently, the model would receive inputs unlike those it learned from.
"""


def combine_text(title: str, description: str) -> str:
    """Join title and description. The title is repeated because it is the best summary."""
    return f"{title}. {title}. {description}"
