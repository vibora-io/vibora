### Frequently Asked Questions

#### Why Vibora ?

 - I needed a framework like Flask but async by design.

 - Sanic is a good idea with questionable design choices (IMHO).

 - Aiohttp is solid (and well thought) but I dislike some
   interfaces and I think many of them could be user-friendlier.

 - I was unaware of Quart and I have mixed feelings about
   being __compatible__ with Flask.

 - Japronto is currently a proof of concept, a very impressive one.

 - Apistar, although I like it, is far away from being like Flask.

 - I don't like Tornado APIs, they did an awesome job don't get me wrong.

 - Big Upload/Downloads is a pain the ass in most frameworks thanks to WSGI.

 - Flask/Django are sync and always will.
   Don't get me wrong, being sync isn't bad but it just doesn't fit in some situations.
   You can do whatever magic you want to make them async but sync interfaces like "request.json" will haunt you.

 - I'm a big fan of type hints and very few projects use them.

 - And finally because history always repeats itself and here we are, again, with another framework.

#### Where the performance comes from ?

  - Cython. Critical framework pieces are written Cython so it can leverage "C speed" in critical stuff.

  - Common tasks as schema validation, template rendering and other stuff were made builtin in the framework,
    written from scratch with performance in mind.

#### Is it compatible with PyPy ?

  - No. PyPy's poor C extensions compatibility (performance-wise) is it's biggest problem.
    Vibora would need to drop its C extensions or have duplicate implementations (Cython powered X pure Python).
    In the end I would bet that Vibora on PyPy would still be slower than the Cython-powered version.
    I'm open to suggestions and I'm watching PyPy closely so who knows.

#### Why not use Jinja2 ?

  - Jinja2 was not built with async in mind.

  - I would need to write a cython compiler for it anyways (Vibora one is in-progress).

  - I want a bit more freedom in the template syntax.

  - And of course: because it looked like an exciting challenge.

#### Where is Japronto on benchmarks ?

  - Vibora was almost twice as fast before network flow control was a concern,
    what that means is that it is very easy to write a fast server but not so easy to build a stable one.

  - Although Japronto inspired some pieces of this framework
    it's missing a huge chunk of fixes and features.

  - The author of the framework does not encourage the usage of it and so do I.

  - Japronto may be faster than Vibora on naked benchmarks thanks to impressive hand-coded C
    and faster HTTP parser (pico X noyent).

  - Vibora may use "picohttparser" in the future but right now I don't think it's a wise move because
    it's less battle tested.

  - Hand-coded C extensions can be a nightmarish hell to non-expert C devs so I'm not
    willing to replace Cython with baby cared C code. Still I'm willing to replace Cython with Rust extensions
    if they get stable enough.

#### Why don't you export the template engine into a new project ?

  - If people show interest, why not.

#### What about Trio ?

  - Trio has some interesting concepts and although it's better
  than asyncio in overall I'm not sure about it. The python async community
  is still young and splitting it is not good. We already have a bunch
  of libraries and uvloop so it's hard to move now. I would like to see
  some of it's concepts implemented on top of asyncio but that needs some
  serious creativity because of asyncio design.

#### Can we make Vibora faster ?

  - Sure. I have a bunch of ideas but I'm a one man army. Are you willing to help me ? :)
