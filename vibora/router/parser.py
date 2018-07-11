import re
from string import ascii_letters, digits
from typing import Tuple, Pattern, List
from ..exceptions import RouteConfigurationError


class PatternParser:

    PARAM_REGEX = re.compile(b"(\(\?P<.*?>.*?\)|[^P]<.*?>)")

    DYNAMIC_CHARS = bytearray(b".*[]<>()")

    CAST = {
        int: lambda x: int(x),
        float: lambda x: float(x),
        str: lambda x: x.decode() if isinstance(x, bytes) else str(x),
        bytes: lambda x: x if isinstance(x, bytes) else str(x).encode(),
    }

    @classmethod
    def validate_param_name(cls, name: bytes) -> None:
        """
        Check if the param name is valid.
        """
        allowed_chars = (ascii_letters + digits + "_").encode()
        for letter in name:
            if letter not in allowed_chars:
                raise RouteConfigurationError(
                    "Special characters are not allowed in param name. "
                    "Use type hints in function parameters to cast variable types "
                    "or named groups to be more specific in your match."
                )

    @classmethod
    def extract_params(cls, pattern: bytes) -> Tuple[Pattern, List[str], List[str]]:
        """
        Extract param names, a working regex and the reverse pattern for a given pattern.
        """
        params = []
        new_pattern = pattern
        reverse_pattern = []
        groups = cls.PARAM_REGEX.findall(pattern)
        current_index = 0
        for group in groups:
            if group.startswith(b"(?P"):
                reverse_pattern.append(pattern[current_index : pattern.find(group)])
                name = group[group.find(b"<") + 1 : group.find(b">")]
                cls.validate_param_name(name)
                reverse_pattern.append(b"$" + name + b"$")
                current_index += pattern.find(group) + len(group)
                params.append(name.decode())
            else:
                group = group[1:]
                name = group[1:-1]
                cls.validate_param_name(name)
                reverse_pattern.append(pattern[current_index : pattern.find(group)])
                name = group[group.find(b"<") + 1 : group.find(b">")]
                reverse_pattern.append(b"$" + name + b"$")
                current_index += pattern.find(group) + len(group)
                params.append(name.decode())
                new_pattern = new_pattern.replace(group, b"(?P<" + name + b">[^/]+)")
        if current_index < len(pattern):
            reverse_pattern.append(pattern[current_index:])
        return re.compile(new_pattern), params, reverse_pattern

    @classmethod
    def is_dynamic_pattern(cls, pattern: bytes) -> bool:
        """
        Check if this pattern needs a regex or can be statically optimized.
        :param pattern: Bytes pattern to be checked.
        :return: True or False
        """
        for index, char in enumerate(pattern):
            if char in cls.DYNAMIC_CHARS:
                if index > 0 and pattern[index - 1] == "\\":
                    continue
                return True
        return False
