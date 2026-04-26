from typer.testing import CliRunner

from .cli import app


def test_main():
    runner = CliRunner()
    result = runner.invoke(app, ["template"])
    assert result.exit_code == 0
    assert result.output == "hello, template\n"
