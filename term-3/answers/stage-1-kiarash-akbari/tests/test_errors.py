import pytest

from data_factory.errors import ConfigError, DataError, FetchError, PipelineError
from data_factory.exit_codes import ExitCode


@pytest.mark.parametrize("cls, code", [
    (ConfigError, ExitCode.CONFIG),
    (FetchError, ExitCode.NETWORK),
    (DataError, ExitCode.DATA),
    (PipelineError, ExitCode.UNEXPECTED),
])
def test_exit_code(cls, code):
    assert cls("x").exit_code == code


def test_context_default():
    assert PipelineError("x").context == {}


def test_context_passed():
    err = FetchError("boom", context={"offset": 50000})
    assert err.context["offset"] == 50000
    assert str(err) == "boom"