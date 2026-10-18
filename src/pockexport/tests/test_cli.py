from hpikit.cli.testing import check_cli_starts


def test_cli_starts() -> None:
    # not hardcoding package name, so this file can be synced across all exporters
    package = __name__.split('.')[0]  # e.g. packagename.tests.test_cli -> packagename
    check_cli_starts(f'{package}.export')
    check_cli_starts(f'{package}.dal')
