from vibora.templates import Template, TemplateEngine
from vibora.templates.exceptions import TemplateRenderError
from vibora.tests import TestSuite


class NodesParsingSuite(TestSuite):
    def setUp(self):
        self.template_engine = TemplateEngine()

    async def test_simple_exception_expects_correct_line_in_stack(self):
        """

        :return:
        """
        content = """
        {% for x in range(0, 10)%}
            {{ x.non_existent_call() }}
        {% endfor %}
        """
        self.template_engine.add_template(Template(content=content), names=["test"])
        self.template_engine.compile_templates(verbose=False)
        try:
            await self.template_engine.render("test")
        except TemplateRenderError as error:
            self.assertEqual(error.template_line, "{{ x.non_existent_call() }}")
            self.assertIsInstance(error.original_exception, AttributeError)
