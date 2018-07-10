### Data Validation

Data validation is a common task in any web related activity.
Vibora has a module called `schemas` to build, guess what,
schemas, and validate your data against them.
They are very similar to `marshmallow` and
other famous libraries except they have some speedups written in Cython
for amazing performance.

Schemas are also asynchronous meaning that you can do
database checkups and everything in a single place,
something that cannot be done in other libraries which forces you to
split your validation logic between different places.

### Usage Example

###### Declaring your schema
```py
from vibora.schemas import Schema, fields
from vibora.schemas.exceptions import ValidationError
from vibora.schemas.validators import Length, Email
from vibora.context import get_component
from .database import Database


class AddUserSchema(Schema):

    @staticmethod
    async def unique_email(email: str):
        # You can get any existent component by using "vibora.context"
        database = get_component(Database)
        if await database.exists_user(email):
            raise ValidationError(
                'There is already a registered user with this e-mail'
            )

    # Custom validations can be done by passing a list of functions
    # to the validators keyword param.
    email: str = fields.Email(pattern='.*@vibora.io',
            validators=[unique_email]
    )

    # There are many builtin validation helpers as Length().
    password: str = fields.String(validators=[Length(min=6, max=20)])

    # In case you just want to enforce the type of a given field,
    # a type hint is enough.
    name: str
```

###### Using your schema

```py
from vibora import Request, Blueprint, JsonResponse
from .schemas import AddUserSchema
from .database import Database

users_api = Blueprint()

@users_api.route('/add')
async def add_user(request: Request, database: Database):

    # In case the schema is invalid an exception will be raised
    # and catched by an exception handler, this means you don't need to
    # repeat yourself about handling errors. But in case you want to
    # customize the error message feel free to catch the exception
    # and handle it your way. "from_request" method is just syntatic sugar
    # to avoid calling request.json() yourself.
    schema = await AddUserSchema.from_request(request)

    # By now our data is already valid and clean,
    # so lets add our user to the database.
    database.add_user(schema)

    return JsonResponse({'msg': 'User added successfully'})
```

> Type hints must always be provided for each field. In case the field is always
required and do not have any custom validation the type hint alone
will be enough to Vibora build your schema.
