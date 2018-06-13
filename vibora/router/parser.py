import re
from ..exceptions import RouteConfigurationError


class PatternParser:

    PARAM_REGEX = re.compile(b'<.*?>')
    DYNAMIC_CHARS = bytearray(b'*?.[]()')

    CAST = {
        str: lambda x: x.decode('utf-8'),
        int: lambda x: int(x),
        float: lambda x: float(x)
    }

    @classmethod
    def validate_param_name(cls, name: bytes):
        # TODO:
        if b':' in name:
            raise RouteConfigurationError('Special characters are not allowed in param name. '
                                          'Use type hints in function parameters to cast the variable '
                                          'or regexes with named groups to ensure only a specific URL matches.')

    @classmethod
    def extract_params(cls, pattern: bytes) -> tuple:
        """

        :param pattern:
        :return:
        """
        params = []
        new_pattern = pattern
        simplified_pattern = pattern
        groups = cls.PARAM_REGEX.findall(pattern)
        for group in groups:
            name = group[1:-1]  # Removing <> chars
            cls.validate_param_name(name)
            simplified_pattern = simplified_pattern.replace(group, b'$' + name)
            params.append(name.decode())
            new_pattern = new_pattern.replace(group, b'(?P<' + name + b'>[^/]+)')
        return re.compile(new_pattern), params, simplified_pattern

    @classmethod
    def is_dynamic_pattern(cls, pattern: bytes) -> bool:
        for index, char in enumerate(pattern):
            if char in cls.DYNAMIC_CHARS:
                if index > 0 and pattern[index - 1] == '\\':
                    continue
                return True
        return False
