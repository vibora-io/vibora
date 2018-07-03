from vibora import Vibora, Request
from vibora.responses import JsonResponse
from vibora.schemas import Schema, fields
from vibora.schemas.exceptions import InvalidSchema

app = Vibora()


class BenchmarkSchema(Schema):
    field1: str = fields.String(required=True)
    field2: int = fields.Integer(required=True)


@app.route('/', methods=['POST'])
async def home(request: Request):
    try:
        values = await BenchmarkSchema.load_json(request)
        return JsonResponse({'msg': 'Successfully validated', 'field1': values.field1,
                             'field2': values.field2})
    except InvalidSchema:
        return JsonResponse({'msg': 'Data is invalid'})


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0', workers=8)
