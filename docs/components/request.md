### Request Component

The request component holds all the information related
to the current request.
Json, Forms, Files everything can be accessed through it.

### Receiving JSON

```py
from vibora import Vibora, Request
from vibora.responses import JsonResponse

app = Vibora()

@app.route('/')
async def home(request: Request):
    values = await request.json()
    print(values)
    return JsonResponse(values)
    
app.run()
```

Note that `request.json()` is actually a coroutine
that needs to be **awaited**, this design prevents the entire JSON being
uploaded in-memory before the route requires it.


### Uploaded Files

Uploaded files by multipart forms can be accessed by
field name in `request.form` or through the
`request.files` list. Both methods are co-routines that will consume the
`request.stream` and store the file in-disk if it's too big
to keep in-memory.

You can control the memory/disk usage of uploaded files by calling
`request.load_form(threshold=1 * 1024 * 1024)` explicitly,
in this case files bigger than 1mb will be flushed to disk.

> Please be aware that the form threshold does not passthrough the
  max_body_size limit so you'll still need to configure your route
  properly.

Instead of pre-parsing the entire form you could call
`request.stream_form()` and deal with every uploaded field as
it arrives by the network. This is good when you don't want files
hitting the disk and in some scenarios allows you to waste less memory
by doing way more coding yourself.

```py
import uuid
from vibora import Vibora, Request
from vibora.responses import JsonResponse

app = Vibora()

@app.route('/', methods=['POST'])
async def home(request: Request):
    uploaded_files = []
    for file in (await request.files):
        file.save('/tmp/' + str(uuid.uuid4()))
        print(f'Received uploaded file: {file.filename}')
        uploaded_files.append(file.filename)
    return JsonResponse(uploaded_files)
```

### Querystring

```py
from vibora import Vibora, Response, Request

app = Vibora()

@app.route('/')
async def home(request: Request):
    print(request.args)
    return Response(f'Name: {request.args['name']}'.encode())
```
> A request to http://{address}/?name=vibora would return 'Name: vibora'

### Raw Stream

Sometimes you need a low-level access to the HTTP request body,
`request.stream` method provides an easy way to consume the
stream by ourself.

```py
from vibora import Vibora, Request, Response

app = Vibora()

@app.route('/', methods=['POST'])
async def home(request: Request):
    content = await request.stream.read()
    return Response(content)
```

### URLs

Ideally you shouldn't need to deal with the URL directly but
sometimes that's the only way. The request object carries two properties
that can help you:

`request.url`: Raw URL

`request.parsed_url`: A parsed URL where you can access the path,
host and all URL attributes easily.
The URL is parsed by a
fast Cython parser so there is no need to you re-invent the wheel.

```py
from vibora import Vibora, Request
from vibora.responses import JsonResponse

app = Vibora()

@app.route('/')
async def home(request: Request):
    return JsonResponse(
        {'url': request.url, 'parsed_url': request.parsed_url}
    )
```
