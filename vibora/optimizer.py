########################################################################
########################################################################
# Portions Copyright (c) 2017 Paweł Piotr Przeradowski.
# https://github.com/squeaky-pl/japronto
########################################################################
########################################################################
import dis
from typing import Callable


def is_static(route_handler: Callable) -> bool:
    """
    Checks if a given route is static.
    :param route_handler: The route handler (a function that produces a http response)
    :return: True or False
    """
    seen_load_fast_0 = False
    seen_return_value = False
    seen_call_fun = False
    valid_responses = ('JsonResponse', 'Response')

    for instruction in dis.get_instructions(route_handler):

        if instruction.opname == 'LOAD_GLOBAL' and instruction.argval in valid_responses:
            seen_load_fast_0 = True
            continue

        if instruction.opname == 'RETURN_VALUE':
            seen_return_value = True
            continue

        if instruction.opname.startswith('CALL_FUNCTION'):
            if seen_call_fun:
                return False

            seen_call_fun = True
            continue

    return seen_call_fun and seen_load_fast_0 and seen_return_value
