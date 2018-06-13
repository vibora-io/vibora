import re

parser = re.compile('[a-z_]+')
whitelist = ['or', 'and', 'range', 'int', 'str']


def prepare_expression(expression: str, context_var: str, scope: list):
    e = expression
    handicap = 0
    for match in parser.finditer(expression):
        start, end = match.start(), match.end()
        if match.group() not in scope and match.group() not in whitelist:
            conditions = (
                expression[(start - 1)] not in ('"', "'", ".") if start > 0 else True,
                expression[end] != '=' if (end - 1) > len(expression) else True
            )
            if all(conditions):
                replace_for = context_var + '.get("' + match.group() + '")'
                e = e[:match.start() + handicap] + replace_for + e[match.end() + handicap:]
                handicap += len(replace_for) - len(match.group())
    return e
