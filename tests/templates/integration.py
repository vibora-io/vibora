from vibora import Vibora, Response
from vibora.tests import TestSuite
from vibora.templates import Template


class ViboraExtensionSuiteCase(TestSuite):

    def setUp(self):
        self.app = Vibora()

        @self.app.route('/')
        async def home():
            return Response(b'')

        self.app.initialize(debug=True)

    async def test_empty_template_expects_empty_string(self):
        template = Template('')
        self.app.template_engine.add_template(template, ['test'])
        self.app.template_engine.compile_templates(verbose=False)
        self.assertEqual('', await self.app.template_engine.render('test'))
