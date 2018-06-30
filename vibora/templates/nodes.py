import re
import ast
from .utils import CompilerFlavor, get_scope_by_args, get_function_name
from .parser import prepare_expression
from .compilers.helpers import smart_iter


class Node:
    def __init__(self, raw: str=''):
        self.children = []
        self.raw = raw

    @staticmethod
    def check(node: str, is_tag: bool):
        return None

    def compile(self, compiler, recursive: bool=True):
        if self.raw:
            compiler.add_comment(self.raw)
        if recursive:
            for child in self.children:
                child.compile(compiler)


class ForNode(Node):

    def __init__(self, variables: str, target: str, raw: str):
        super().__init__(raw)
        self.target = target
        self.variables = variables

    @staticmethod
    def check(node: str, is_tag: bool):
        if 'for' in node and 'in' in node:
            variables = node[node.find('for') + 3:node.find('in')]
            variables = [x.strip() for x in variables.split(',')]
            target = node[node.find('in')+3:node.rfind('%')].strip()
            return ForNode(variables, target, node), '{% endfor %}'

    @staticmethod
    def optimize_stm(content):
        try:
            args = []
            tree = ast.parse(content, mode='eval')
            if tree.body.func.id == 'range':
                for arg in tree.body.args:
                    if isinstance(arg, ast.Num):
                        if arg.n > 10000:
                            return None
                        args.append(arg.n)
                    else:
                        return None
            return list(range(*args))
        except (AttributeError, ValueError):
            return None

    def compile(self, compiler, recursive: bool=True):
        super().compile(compiler, recursive=False)
        var_name = ', '.join(self.variables)
        stm = prepare_expression(self.target, compiler.context_var, compiler.current_scope)
        optimized_stm = self.optimize_stm(stm)
        if optimized_stm:
            compiler.add_statement(f'for {var_name} in {stm}:')
        else:
            compiler.add_statement(f'async for {var_name} in {smart_iter.__name__}({stm}):')
        compiler.indent()
        for variable in self.variables:
            compiler.current_scope.append(variable)
        for child in self.children:
            child.compile(compiler)
        for variable in self.variables:
            compiler.current_scope.remove(variable)
        compiler.rollback()


class IfNode(Node):

    parser = re.compile('{%\s?if\s(.*?)\s?%}')

    def __init__(self, expression: str, raw: str):
        super().__init__(raw)
        self.expression = expression

    @staticmethod
    def check(node: str, is_tag: bool):
        found = IfNode.parser.search(node)
        if found:
            return IfNode(found.groups()[0], node), '{% endif %}'

    def compile(self, compiler, recursive: bool=True):
        super().compile(compiler, recursive=False)
        expr = prepare_expression(self.expression, compiler.content_var, compiler.current_scope)
        compiler.add_statement('if ' + expr + ':')
        compiler.indent()
        for child in self.children:
            if isinstance(child, ElseNode):
                compiler.flush_text()
                compiler.rollback()
                compiler.add_statement('else:')
                compiler.indent()
            else:
                child.compile(compiler)
        compiler.flush_text()
        compiler.rollback()


class ElifNode(Node):

    parser = re.compile('{%\s?elif\s(.*?)\s?%}|{%\s?else if \s(.*?)\s?%}')

    def __init__(self, expression: str, raw: str):
        super().__init__(raw)
        self.expression = expression

    @staticmethod
    def check(node: str, is_tag: bool):
        found = ElifNode.parser.search(node)
        if found:
            return ElifNode(found.groups()[0], node), None

    def compile(self, compiler, recursive: bool=True):
        super().compile(compiler, recursive=False)
        expr = prepare_expression(self.expression, compiler.content_var, compiler.current_scope)
        compiler.add_statement('elif ' + expr + ':')
        compiler.indent()
        rollback = True
        for child in self.children:
            if isinstance(child, ElifNode) or isinstance(child, ElseNode):
                compiler.indent()
                rollback = False
            child.compile(compiler)
        if rollback:
            compiler.rollback()


class ElseNode(Node):

    parser = re.compile('{%\s?else\s(.*?)\s?%}')

    def __init__(self, expression: str, raw: str):
        super().__init__(raw)
        self.expression = expression

    @staticmethod
    def check(node: str, is_tag: bool):
        found = ElseNode.parser.search(node)
        if found:
            return ElseNode(found.groups()[0], node), None

    def compile(self, compiler, recursive: bool=True):
        raise SyntaxError('ElseNodes should not be compiled')


class EvalNode(Node):

    def __init__(self, code: str, raw: str):
        super().__init__(raw)
        self.code = code

    @staticmethod
    def check(node: str, is_tag: bool):
        # FixMe: Check is_tag instead of this crap.
        if node[:2] == '{{' and node[-2:] == '}}':
            return EvalNode(node[2:-2].strip(), node), None

    def _compile_macro(self, compiler):
        if compiler.current_scope:
            stm = f'{compiler.content_var}.append(str({self.code}))'
            compiler.add_statement(stm)
        else:
            raise Exception('Macros do not have access to the context.')

    def _compile_template(self, compiler):
        stm = prepare_expression(self.code, compiler.context_var, compiler.current_scope)
        compiler.add_statement(f'__temp__ = {stm}')
        compiler.add_statement(f'if iscoroutine(__temp__):')
        compiler.indent()
        compiler.add_eval(f'str(await __temp__)')
        compiler.rollback()
        compiler.add_statement(f'else:')
        compiler.indent()
        compiler.add_eval(f'str({stm})')
        compiler.rollback()

    def compile(self, compiler, recursive: bool=True):
        super().compile(compiler, recursive=False)
        if compiler.flavor == CompilerFlavor.MACRO:
            self._compile_macro(compiler)
        elif compiler.flavor == CompilerFlavor.TEMPLATE:
            self._compile_template(compiler)


class TextNode(Node):

    def __init__(self, text: str):
        super().__init__('')
        self.text = text

    def compile(self, compiler, recursive: bool = True):
        compiler.add_text(self.text)


class BlockNode(Node):
    def __init__(self, name: str, raw: str):
        super().__init__(raw)
        self.name = name

    @staticmethod
    def check(node: str, is_tag: bool):
        import re
        parser = re.compile('{% block (.*?) %}')
        found = parser.search(node)
        if found:
            return BlockNode(found.groups()[0], node), '{% endblock %}'


class ExtendsNode(Node):

    parser = re.compile('[\'"](.*)[\'"]')

    def __init__(self, parent: str, raw: str):
        super().__init__(raw)
        self.parent = parent

    @staticmethod
    def check(node: str, is_tag: bool):
        if 'extends' in node:
            groups = ExtendsNode.parser.search(node).groups()
            if groups:
                return ExtendsNode(groups[0], node), None


class IncludeNode(Node):

    parser = re.compile('[\'"](.*)[\'"]')

    def __init__(self, target: str, raw: str):
        super().__init__(raw)
        self.target = target

    @staticmethod
    def check(node: str, is_tag: bool):
        if 'include' in node:
            groups = IncludeNode.parser.search(node).groups()
            if groups:
                return IncludeNode(groups[0], node), None


class StaticNode(Node):

    parser = re.compile('{% static [\'|\"](.*)[\'|\"] %}')

    def __init__(self, url: str, raw: str):
        super().__init__(raw)
        self.url = url

    @staticmethod
    def check(node: str, is_tag: bool):
        if 'static' in node:
            groups = StaticNode.parser.search(node).groups()
            if groups:
                return StaticNode(groups[0], node), None

    def compile(self, compiler, recursive: bool = True):
        raise SyntaxError('Static nodes should not be compiled. An extension should process them.')


class UrlNode(Node):

    parser = re.compile('{% url [\'|\"](.*)[\'|\"] %}')

    def __init__(self, url: str, raw: str):
        super().__init__(raw)
        self.url = url

    @staticmethod
    def check(node: str, is_tag: bool):
        if 'url' in node:
            match = UrlNode.parser.search(node)
            if match:
                return UrlNode(match.groups()[0], node), None

    def compile(self, compiler, recursive: bool = True):
        raise SyntaxError('URL nodes should not be compiled. An extension should deal with them.')


class MacroNode(Node):
    parser = re.compile('{% macro (.*?) %}')

    def __init__(self, func_definition: str, raw: str):
        super().__init__(raw)
        self.func_definition = func_definition

    @staticmethod
    def check(node: str, is_tag: bool):
        if 'macro' in node:
            match = MacroNode.parser.search(node)
            if match:
                return MacroNode(match.groups()[0], node), '{% endmacro %}'

    def compile(self, compiler, recursive: bool = True):
        # TODO: Refactor.
        compiler.current_scope.append(get_function_name(self.func_definition))
        new_compiler = compiler.create_new_macro(self.func_definition)
        scope = get_scope_by_args(self.func_definition)
        new_compiler.current_scope += scope
        for child in self.children:
            child.compile(new_compiler)
        new_compiler.add_statement('return \'\'.join(' + new_compiler.content_var + ')')
        compiler.functions.append(new_compiler.content)
