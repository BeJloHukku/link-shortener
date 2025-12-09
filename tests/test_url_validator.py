import pytest
from src.exeptions import WrongUrlGivenError
from src.url_validator import validate_url


def test_validate_url():
    result_www = validate_url("https://www.google.com")
    result_simple = validate_url("https://vehicle-monitoring.ru")
    assert result_www is None
    assert result_simple is None

def test_validate_url_wrong_url():
    with pytest.raises(WrongUrlGivenError):
        validate_url("htt://link.ru")
