### Deployment

Vibora is not a WSGI compatible framework because of its async nature.
Its own http server is built to battle so deployment is far easier
than with other frameworks because there is no need for Gunicorn/uWSGI.

One may argue that Gunicorn/uWSGI are battle proven solutions and that's true
but they also bring different applications behaviors between dev/prod
environments and still need a battle tested server as Nginx
in front of them.

The recommend approach to freeze a Vibora app is using docker,
this way you can build a frozen image locally in your machine, test it
and upload to wherever you host. This way you skip
all python packaging problems that you'll find trying to build
reproducible deployments between different machines.
