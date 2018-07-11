from vibora import Vibora, Response
from vibora.tests import TestSuite
from vibora.templates import Template


class ViboraExtensionSuiteCase(TestSuite):
    def setUp(self):
        self.app = Vibora()

        @self.app.route("/")
        async def home():
            return Response(b"")

        self.app.initialize()

    async def test_url_for_inside_for_node(self):
        template = Template('{% for x in range(0, 10)%}{% url "home" %}{% endfor %}')
        self.app.template_engine.add_template(template, ["test"])
        self.app.template_engine.compile_templates()
        self.assertEqual(self.app.url_for("home") * 10, await self.app.template_engine.render("test"))

    async def test_static_node(self):
        template = Template("{% static 'js/app.js' %}")
        self.app.template_engine.add_template(template, ["test"])
        self.app.template_engine.compile_templates()
        self.assertEqual("/static/js/app.js", await self.app.template_engine.render("test"))
