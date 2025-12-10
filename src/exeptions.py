class ShortenetBaseError(Exception):
    pass


class NoLongUrlFoundError(ShortenetBaseError):
    pass


class SlugAlreadyExistError(ShortenetBaseError):
    pass


class CusomUrlAlreadyExistError(ShortenetBaseError):
    pass


class WrongUrlGivenError(ShortenetBaseError):
    pass