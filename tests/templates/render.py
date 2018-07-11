from vibora.tests import TestSuite
from vibora.templates import TemplateEngine, Template


class RenderSuite(TestSuite):
    def setUp(self):
        self.engine = TemplateEngine()

    async def test_empty_template_expects_empty_string(self):
        template = Template("")
        self.engine.add_template(template, ["test"])
        self.engine.compile_templates(verbose=False)
        self.assertEqual("", await self.engine.render("test"))

    async def test_render_for_with_with_unpacked_variables(self):
        template = Template("{% for a, b in [(1, 2)] %} {{ a }} + {{ b }} {% endfor %}")
        self.engine.add_template(template, ["test"])
        self.engine.compile_templates(verbose=False)
        self.assertEqual(" 1 + 2 ", await self.engine.render("test"))

    async def test_render_for_with_a_single_variable(self):
        template = Template("{% for a in [(1, 2)] %} {{ a }} {% endfor %}")
        self.engine.add_template(template, ["test"])
        self.engine.compile_templates(verbose=False)
        self.assertEqual(" (1, 2) ", await self.engine.render("test"))
