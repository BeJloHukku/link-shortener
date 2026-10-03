class ShortenerBaseError(Exception):
    pass


class NoLongUrlFoundError(ShortenerBaseError):
    pass


class SlugAlreadyExistError(ShortenerBaseError):
    pass


class CusomUrlAlreadyExistError(ShortenerBaseError):
    pass


class WrongUrlGivenError(ShortenerBaseError):
    pass