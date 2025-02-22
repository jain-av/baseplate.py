from pylint.lint import PyLinter

from baseplate.lint.db_query_string_format_plugin import NoDbQueryStringFormatChecker


def register(linter: PyLinter) -> None:
    linter.register_checker(NoDbQueryStringFormatChecker(linter))
