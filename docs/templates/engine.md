### Vibora Template Engine (VTE)

Although server-side rendering is not main-stream nowadays, Vibora has
its own template engine. The idea was to build something like Jinja2
but with async users as first class citizens. Jinja2 is already heavily
optimized but we tried to beat it in benchmarks.

Jinja2 also prevents you to pass parameters to functions and a few other
restrictions which are often a good idea but don't comply with Vibora
philosophy of not getting into your way.

The syntax is pretty similar to Jinja2, templates are often compatible.

The render process is async which means you can pass coroutines to your
templates and call them as regular functions, Vibora will do the magic.

VTE has hot-reloading so we can swap templates at run-time.
This is enabled by default in debug mode so you have a fast iteration
cycle while building your app.

Although VTE **do not aim to be sandboxed** it tries hard to prevent the templates from leaking access to outside context.
