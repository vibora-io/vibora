from ..utils import TemplateMeta, CompilationResult


class TemplateCompiler:

    NAME = "compiler"
    VERSION = "0.0.0"

    def __init__(self):
        self._indentation = 0
        self.pending_statement = False

    def clean(self):
        raise NotImplementedError

    def indent(self):
        self._indentation += 4
        self.pending_statement = True

    def rollback(self):
        self.flush_text()
        if self.pending_statement and self._indentation > 4:
            self.add_statement("pass")
        elif self.pending_statement and self._indentation == 4:
            # This is a special case when the template is actually empty.
            self.add_statement("yield ''")
        self._indentation -= 4

    def add_text(self, content: str):
        raise NotImplementedError

    def flush_text(self):
        raise NotImplementedError

    def add_statement(self, content: str):
        raise NotImplementedError

    def consume(self, template):
        raise NotImplementedError

    @classmethod
    def create_new_macro(cls, definition: str):
        raise NotImplementedError

    @classmethod
    def load_compiled_template(cls, meta: TemplateMeta, content: bytes):
        raise NotImplementedError

    def compile(self, template, verbose: bool = False) -> CompilationResult:
        raise NotImplementedError

    @classmethod
    def generate_template_name(cls, hash_: str):
        return hash_
