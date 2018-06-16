import platform
from setuptools import setup, Extension, find_packages

if platform.system().lower() == 'linux':
    dependencies = ['uvloop', 'ujson', 'pendulum']
else:
    dependencies = ['pendulum']

setup(
    name="vibora",
    version='0.0.6',
    description='Fast, asynchronous and sexy Python web framework',
    author='Frank Vieira',
    author_email='frank@frankvieira.com.br',
    url='https://vibora.io',
    license='MIT',
    python_requires='>=3.6',
    classifiers=[
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
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
