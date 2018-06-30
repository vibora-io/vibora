from .exceptions import ValidationError
from .messages import Messages
import math


class Length:
    def __init__(self, min: int=0, max: int=math.inf):
        self.min = min
        self.max = max

    def __call__(self, x):
        size = len(x)
        if size < self.min:
            raise ValidationError(error_code=Messages.MINIMUM_LENGTH, minimum_value=self.min)
        if size > self.max:
            raise ValidationError(error_code=Messages.MAXIMUM_LENGTH, maximum_value=self.max)
