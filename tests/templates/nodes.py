from collections import deque
from vibora.templates.nodes import ForNode, EvalNode, TextNode, IfNode, ElseNode
from vibora.templates import Template, TemplateParser
from vibora.tests import TestSuite


class NodesParsingSuite(TestSuite):
    def test_for_node(self):
        """

        :return:
        """
        tp = TemplateParser()
        parsed = tp.parse(Template(content="{% for x in range(0, 10)%}{{x}}{%endfor %}"))
        expected_types = deque([ForNode, EvalNode])
        generated_nodes = parsed.flat_view(parsed.ast)
        while expected_types:
            expected_type = expected_types.popleft()
            current_node = next(generated_nodes)
            self.assertIsInstance(current_node, expected_type)

    def test_for_node_with_text_between(self):
        """

        :return:
        """
        tp = TemplateParser()
        parsed = tp.parse(Template(content="{% for x in range(0, 10)%} {{x}} {%endfor %}"))
        expected_types = deque([ForNode, TextNode, EvalNode, TextNode])
        generated_nodes = parsed.flat_view(parsed.ast)
        while expected_types:
            expected_type = expected_types.popleft()
            current_node = next(generated_nodes)
            self.assertIsInstance(current_node, expected_type)

    def test_for_node_with_if_condition(self):
        """

        :return:
        """
        tp = TemplateParser()
        parsed = tp.parse(Template(content="{% for x in range(0, 10)%}{% if x == 0 %}{{ y }}{% endif %}{% endfor %}"))
        expected_types = deque([ForNode, IfNode, EvalNode])
        generated_nodes = parsed.flat_view(parsed.ast)
        while expected_types:
            expected_type = expected_types.popleft()
            current_node = next(generated_nodes)
            self.assertIsInstance(current_node, expected_type)

    def test_for_node_with_if_else_condition(self):
        """

        :return:
        """
        tp = TemplateParser()
        content = """
        {% for x in range(0, 10)%}
            {% if x == 0 %}
                {{ x }}
            {% else %}
                -
            {% endif %}
        {% endfor %}
        """.replace(
            "\n", ""
        ).replace(
            "  ", ""
        )
        parsed = tp.parse(Template(content=content))
        expected_types = deque([ForNode, IfNode, EvalNode, ElseNode, TextNode])
        generated_nodes = parsed.flat_view(parsed.ast)
        while expected_types:
            expected_type = expected_types.popleft()
            current_node = next(generated_nodes)
            self.assertIsInstance(current_node, expected_type)
