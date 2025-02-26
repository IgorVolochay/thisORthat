import re

from dirty_words import dirty_words_set

def is_not_empty(text: str) -> bool:
    """Checks that the text is not empty."""
    return bool(text.strip())

def has_no_links(text: str) -> bool:
    """Checks that there are no links in the text."""
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return not bool(url_pattern.search(text))

def has_no_dirty_words(text: str) -> bool:
    """Checks that there are no forbidden words in the text."""
    words = set(re.findall(r'\w+', text.lower()))
    return not bool(words & dirty_words_set)

def text_lenght(text: str) -> bool:
    """Check max text lenght"""
    return len(text) <= 150 # TODO: update in future

def moderate_text(text: str) -> bool:
    return is_not_empty(text) and has_no_links(text) and has_no_dirty_words(text) and text_lenght(text)
