import time
import uvloop
from inspect import isasyncgenfunction, isasyncgen, iscoroutinefunction
from jinja2 import Template
from vibora.templates import Template as VTemplate, TemplateEngine


async def b():
    return 'oi'


def gen():
    for x in range(0, 1000):
        yield x


y = gen()
rounds = 1000
content = '{% for b in y%}{{x()}}{% endfor %}'
# content = '{{ x() }}'
engine = TemplateEngine()
engine.add_template(VTemplate(content), names=['test'])
engine.compile_templates(verbose=True)


async def render():
    template = engine.loaded_templates['test']
    c = engine.prepared_calls[template]
    t1 = time.time()
    for _ in range(0, rounds):
        asd = ''
        async for x in c({'x': b, 'y': y}):
            asd += x
    print('Vibora: ', time.time() - t1)

loop = uvloop.new_event_loop()
loop.run_until_complete(render())

t1 = time.time()
t = Template(content, enable_async=True)
for _ in range(0, rounds):
    t.render({'x': b, 'y': y})
print('Jinja2: ', time.time() - t1)

