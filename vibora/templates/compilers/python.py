import time
import datetime
from .base import TemplateCompiler
from ..template import CompiledTemplate
from ..utils import CompilerFlavor, CompilationResult, TemplateMeta, get_architecture_signature, \
    generate_entry_point
from ..exceptions import InvalidVersion, InvalidArchitecture


class PythonTemplateCompiler(TemplateCompiler):
    VERSION = '0.0.1'
    NAME = 'Pure'

    def __init__(self, flavor=CompilerFlavor.TEMPLATE):
        super().__init__()
        self.meta = None
        self.content = ''
        self.current_scope = list()
        self.accumulated_text = ''
        self.content_var = '__content__'
        self.context_var = '__context__'
        self.static_vars: dict = {}
        self.functions = []
        self.flavor = flavor
        self.pending_comment = None

    @staticmethod
    def get_text_representation(value):
        """

        :param value:
        :return:
        """
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, int):
            return f'{value}'
        elif isinstance(value, list):
            return str(value)
        else:
            NotImplementedError(f'Cannot convert {value} to a text representation.')

    def add_static_var(self, value) -> str:
        """

        :param value:
        :return:
        """
        name = 'static_var_' + str(len(self.static_vars))
        self.static_vars[name] = value
        return name

    def clean(self):
        """

        :return:
        """
        self.meta = None
        self.content = ''
        self.current_scope = list()
        self.accumulated_text = ''
        self.functions = []
        self.flavor = CompilerFlavor.TEMPLATE

    def add_text(self, content: str):
        """

        :param content:
        :return:
        """
        content = content.replace("\n", "\\n")
        content = content.replace(r'"', r'\"')
        self.accumulated_text += content

    def flush_text(self):
        """

        :return:
        """
        text = self.accumulated_text
        self.accumulated_text = ''
        if text:
            self.add_statement(f'yield "{text}"', flush_comments=False)

    def add_eval(self, statement: str):
        """

        :param statement:
        :return:
        """
        self.add_statement(f'yield {statement}')

    def add_comment(self, content: str):
        """

        :param content:
        :return:
        """
        comment = (' ' * self._indentation) + '# ' + content.strip() + '\n'
        self.pending_comment = comment

    def add_statement(self, content: str, flush_comments: bool=True):
        """

        :param flush_comments:
        :param content:
        :return:
        """
        if self.accumulated_text:
            self.flush_text()
        if self.pending_comment and flush_comments:
            self.content += self.pending_comment
            self.pending_comment = None
        new_content = (' ' * self._indentation) + content.strip() + '\n'
        self.content += new_content
        self.pending_statement = False

    def statement(self, stm: str):
        """

        :param stm:
        :return:
        """
        self.add_statement(stm)
        return IndentationBlock(self)

    def consume(self, template):
        """

        :param template:
        :return:
        """
        self.content += 'from vibora.templates.compilers.helpers import *\n\n'

        # Adding helper functions and macros.
        for helper_code in self.functions:
            self.content += helper_code + '\n\n'

        entry_point = generate_entry_point(template)
        with self.statement(f'async def {entry_point}({self.context_var}: dict):'):
            template.ast.compile(self)

        # Adding static variables to the top side of the file.
        static_vars_content = ''
        for name, value in self.static_vars.items():
            static_vars_content += f'{name} = {self.get_text_representation(value)}\n'
        self.content = static_vars_content + self.content

    def create_new_macro(self, definition: str):
        """

        :param definition:
        :return:
        """
        new_compiler = self.__class__(flavor=CompilerFlavor.MACRO)
        new_compiler.add_statement('def ' + definition + ':')
        new_compiler.indent()
        new_compiler.add_statement(f"{self.content_var} = []")
        return new_compiler

    def get_render_function(self, content: str, entry_point: str):
        """

        :param content:
        :param entry_point:
        :return:
        """
        context = {}
        exec(compile(content, '<string>', 'exec'), context)
        return context[entry_point]

    def load_compiled_template(self, meta: TemplateMeta, content: bytes):
        """

        :param meta:
        :param content:
        :return:
        """
        if meta.version != self.VERSION:
            raise InvalidVersion
        if meta.architecture != get_architecture_signature():
            raise InvalidArchitecture
        return self.get_render_function(content.decode('utf-8'), meta.entry_point)

    def compile(self, template, verbose: bool=False) -> CompiledTemplate:
        """

        :param verbose:
        :param template:
        :return:
        """
        # Tracking our compile times :)
        started_at = time.time()

        # Entry point is the function name which is responsible for the actual template render.
        entry_point = generate_entry_point(template)

        # Running through the AST while building the respective code.
        self.consume(template)

        # Generating meta data about this compilation so we can correctly
        # cache and load these templates later.
        meta = TemplateMeta(
            entry_point=entry_point,
            version=self.VERSION,
            compiler=self.NAME,
            template_hash=template.hash,
            created_at=datetime.datetime.now().isoformat(),
            architecture=get_architecture_signature(),
            compilation_time=round(time.time() - started_at, 2),
            dependencies=template.dependencies
        )

        # Compilation result contains the meta data and the render function loaded at runtime.
        if verbose:
            print(self.content)

        compiled = CompiledTemplate(
            content=template.content, ast=template.ast, dependencies=template.dependencies,
            code=self.content, meta=meta, render=self.get_render_function(self.content, entry_point)
        )

        # Cleaning the state machine.
        self.clean()

        return compiled


class IndentationBlock:
    def __init__(self, compiler: PythonTemplateCompiler):
        self.compiler = compiler

    def __enter__(self):
        self.compiler.indent()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.compiler.rollback()
