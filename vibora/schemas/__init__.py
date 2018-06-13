from .extensions import fields
from .schemas import *
from .extensions.schemas import Schema as CythonSchema


locals()['Schema'] = CythonSchema
