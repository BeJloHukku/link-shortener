from re import match

from src.exeptions import WrongUrlGivenError

URL_PATTERN = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"

def validate_url(long_url: str) -> None:
    validator = match(URL_PATTERN, long_url)
    if not validator:
        raise WrongUrlGivenError
    