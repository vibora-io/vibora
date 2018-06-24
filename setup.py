import platform
import re
import pathlib
import os
from setuptools import setup, Extension, find_packages

# Uvloop and ujson are notoriously problematic at Windows so they are skipped for Windows users.
# They still can install and benefit from it... it's just that Vibora doesnt make it mandatory.
dependencies = ['pendulum']
if platform.system().lower() == 'linux':
    if os.environ.get('VIBORA_UVLOOP', 1) != '0':
        dependencies.append('uvloop')
    if os.environ.get('VIBORA_UJSON', 1) != '0':
        dependencies.append('ujson')

# Loading version
here = pathlib.Path(__file__).parent
txt = (here / 'vibora' / '__version__.py').read_text()
version = re.findall(r"^__version__ = '([^']+)'\r?$", txt, re.M)[0]


setup(
    name="vibora",
    version=version,
    description='Fast, asynchronous and efficient Python web framework',
    author='Frank Vieira',
    author_email='frank@frankvieira.com.br',
    url='https://vibora.io',
    license='MIT',
    python_requires='>=3.6',
    classifiers=[
        'Intended Audience :: Developers',
        'Development Status :: 4 - Alpha',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6'
    ],
    install_requires=dependencies,
    ext_modules=[
        Extension(
            "vibora.parsers.parser",
            [
                "vibora/parsers/parser.c",
                "vendor/http-parser-2.8.1/http_parser.c",
            ],
            extra_compile_args=['-O3'],
            include_dirs=['.', '/git/vibora/vibora']
        ),
        Extension(
            "vibora.parsers.response",
            [
                "vibora/parsers/response.c",
                "vendor/http-parser-2.8.1/http_parser.c"
            ],
            extra_compile_args=['-O3'],
            include_dirs=['.', '/git/vibora/vibora']
        ),
        Extension(
            "vibora.router.router",
            ["vibora/router/router.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.']
        ),
        Extension(
            "vibora.responses.responses",
            ["vibora/responses/responses.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.']
        ),
        Extension(
            "vibora.protocol.cprotocol",
            ["vibora/protocol/cprotocol.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.']
        ),
        Extension(
            "vibora.protocol.cwebsocket",
            ["vibora/protocol/cwebsocket.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.']
        ),
        Extension(
            "vibora.request.request",
            ["vibora/request/request.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.']
        ),
        Extension(
            "vibora.cache.cache",
            ["vibora/cache/cache.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.']
        ),
        Extension(
            "vibora.headers.headers",
            ["vibora/headers/headers.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.']
        ),
        Extension(
            "vibora.schemas.extensions.fields",
            ["vibora/schemas/extensions/fields.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.', 'vibora/schemas']
        ),
        Extension(
            "vibora.schemas.extensions.schemas",
            ["vibora/schemas/extensions/schemas.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.', 'vibora/schemas']
        ),
        Extension(
            "vibora.schemas.extensions.validator",
            ["vibora/schemas/extensions/validator.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.', 'vibora/schemas']
        ),
        Extension(
            "vibora.components.components",
            ["vibora/components/components.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.']
        ),
        Extension(
            "vibora.multipart.parser",
            ["vibora/multipart/parser.c"],
            extra_compile_args=['-O3'],
            include_dirs=['.']
        )
    ],
    packages=find_packages()
)
