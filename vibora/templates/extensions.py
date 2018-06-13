from .engine import TemplateEngine, Template
from .nodes import UrlNode, TextNode, StaticNode
from .ast import replace_on_tree


class EngineExtension:

    def before_compile(self, engine: TemplateEngine, template: Template):
        pass


class ViboraNodes(EngineExtension):

    def __init__(self, app):
        super().__init__()
        self.app = app

    def before_prepare(self, engine: TemplateEngine, template: Template):
        """
        Handling specific Vibora nodes.
        The template engine is not tied to Vibora, the integration is done through extensions.
        :param engine:
        :param template:
        :return:
        """
        replace_on_tree(lambda node: isinstance(node, UrlNode),
                        lambda node: TextNode(self.app.url_for(node.url)),
                        current_node=template.ast)

        def replace_static(node):
            if not self.app.static:
                msg = 'Please configure a static handler before using a {% static %} tag in your templates.'
                raise NotImplementedError(msg)
            url = self.app.static.url_for(node.url)
            return TextNode(url)

        replace_on_tree(lambda x: isinstance(x, StaticNode), replace_static, current_node=template.ast)
