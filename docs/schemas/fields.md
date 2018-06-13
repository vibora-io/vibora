### Fields

Vibora has a special class called "Field" to represent each field
of a schema. You can build any kind of validation rules using this class
but to avoid repeat yourself there a few builtin ones.
There are a few must-know attributes of this class:

1) **required** -> By default all declared fields in a schema are required which means
they must be present in the validation values.
If you have optional fields you must explicitely declare this as
`Field(required=False)`

2) **load_from** -> Sometimes is useful to deal with friendly names
inside a schema but to ofuscate them outside outside your app, by using the `load_from` parameter
you can specify where to load this field from or even load two
different fields from the same key.

3) **default** -> A default value in case the key is missing
or the value is null.

4) **validators** -> A list of functions to validate the current value against.
This functions can be async or sync and receive one up to two parameters.
In case it receives a single parameter then Vibora will pass only the current value to it.
In case it receive two parameters the context of the schema will be also provided.
The exception `ValidationError` must be raised to notify the schema that this field is invalid,
returning values are ignored.

### StringField

Validates if the given value is a valid string.

```py
import uuid
from vibora.schemas import Schema, fields
from vibora.schemas.validators import Length

class NewUserSchema(Schema):

    name: str = fields.String(
        required=False,
        validators=[Length(min=3, max=30)],
        default=lambda: str(uuid.uuid4()),
        strict=False
    )
```

> There is a special attribute called `strict` to allow this field to cast
integers and similar types to a string instead of raising an error.