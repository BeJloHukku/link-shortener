

class ShortenetBaseError(Exception):
    pass


class NoLongUrlFoundError(ShortenetBaseError):
    pass

class SlugAlreadyExistError(ShortenetBaseError):
    pass