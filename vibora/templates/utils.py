import os
import json
import platform
import typing
from .exceptions import FailedToCompileTemplate


def find_template_binary(path: str):
    name = os.listdir(path)[-1]
    if not name:
        raise FailedToCompileTemplate(path)
    return os.path.join(path, name)


class CompilerFlavor:
    TEMPLATE = 1
    MACRO = 2


def get_scope_by_args(function_def: str):
    open_at = function_def.find('(') + 1
    close_at = function_def.rfind(')')
    args = function_def[open_at:close_at]
    scope = []
    for value in args.split(','):
        if value.find('='):
            scope.append(value.split('=')[0].strip())
        else:
            scope.append(value.strip())
    return scope


def get_function_name(definition: str):
    return definition[:definition.find('(')].strip()


class TemplateMeta:
    def __init__(self, entry_point: str, version: str, template_hash: str,
                 created_at: str, compiler: str, architecture: str, compilation_time: float,
                 dependencies: list=None):
        self.entry_point = entry_point
        self.version = version
        self.template_hash = template_hash
        self.created_at = created_at
        self.compiler = compiler
        self.architecture = architecture
        self.compilation_time = compilation_time
        self.dependencies = dependencies or []

    @classmethod
    def load_from_path(cls, path: str):
        with open(path) as f:
            return TemplateMeta(**json.loads(f.read()))

    def store(self, path: str):
        with open(path, 'w') as f:
            values = self.__dict__.copy()
            values['dependencies'] = list(self.dependencies)
            f.write(json.dumps(values))


class CompilationResult:
    def __init__(self, template, meta: TemplateMeta, render_function: typing.Callable,
                 code: bytes):
        self.template = template
        self.meta = meta
        self.render_function = render_function
        self.code = code


def get_architecture_signature() -> str:
    return ''.join(platform.architecture())


def generate_entry_point(template) -> str:
    return 'render_' + template.hash


def get_import_names(root: str, template_path: str):
    names = {os.path.join(root, template_path), os.path.basename(template_path)}
    pieces = template_path.split('/')
    for index in range(1, len(pieces)):
        names.add(os.path.sep.join(pieces[index:]))
    return list(names)
