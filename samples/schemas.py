from vibora import Vibora
from vibora.responses import JsonResponse
from vibora.schemas import Schema, fields


app = Vibora()


async def validate(value, context):
    return True


class BenchmarkSchema(Schema):
    field1: str = fields.String(required=True, )
    field2 = fields.Integer(required=True)


@app.route('/', methods=['POST'])
async def home(request):
    values = BenchmarkSchema.from_request(request)
    context = await BenchmarkSchema.load()
    if context.is_valid:
        return JsonResponse({'msg': 'Successfully validated'})
    return JsonResponse({'errors': context.errors})


if __name__ == '__main__':
    app.run(debug=False, port=8000, host='0.0.0.0', workers=8)
