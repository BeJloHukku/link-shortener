import string
from secrets import choice

ALPHABET: str = string.ascii_letters + string.digits


def generate_random_slug():
    slug = ""
    for _ in range(6):
        slug += choice(ALPHABET)
    return slug
