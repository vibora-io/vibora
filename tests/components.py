from vibora import Vibora, Response, Request
from vibora.tests import TestSuite


class ComponentsTestSuite(TestSuite):
    def test_duplicated_component_expects_exception(self):
        class Config:
            def __init__(self):
                self.name = b"test"

        app = Vibora()
        try:
            app.components.add(Config(), Config())
            self.fail("ComponentsEngine failed to validate duplicated components.")
        except ValueError:
            pass

    async def test_single_component_in_route(self):
        class Config:
            def __init__(self):
                self.name = b"test"

        app = Vibora()
        app.components.add(Config())

        @app.route("/")
        async def home(config: Config):
            return Response(config.name)

        async with app.test_client() as client:
            response = await client.get("/")
            self.assertEqual(response.content, app.components[Config].name)

    async def test_multiple_components_in_route(self):
        class TestComponent:
            def __init__(self):
                self.name = b"test"

        class TestComponent2:
            def __init__(self):
                self.name = b"test"

        app = Vibora()
        app.components.add(TestComponent(), TestComponent2())

        @app.route("/")
        async def home(test: TestComponent, test2: TestComponent2):
            return Response(test.name + test2.name)

        async with app.test_client() as client:
            response = await client.get("/")
            self.assertEqual(response.content, app.components[TestComponent].name + app.components[TestComponent2].name)

    async def test_multiple_components_with_parameters_in_route(self):
        class TestComponent:
            def __init__(self):
                self.name = b"test"

        class TestComponent2:
            def __init__(self):
                self.name = b"test"

        app = Vibora()
        app.components.add(TestComponent2(), TestComponent())

        @app.route("/<name>")
        async def home(test: TestComponent, test2: TestComponent2, name: str):
            return Response(test.name + test2.name + name.encode())

        async with app.test_client() as client:
            response = await client.get("/test")
            self.assertEqual(
                response.content, app.components[TestComponent].name + app.components[TestComponent2].name + b"test"
            )

    def test_loaded_component_class_instead_of_instance_expects_exception(self):
        class TestComponent:
            def __init__(self):
                self.name = b"test"

        app = Vibora()
        try:
            app.components.add(TestComponent)
            self.fail("Loaded component must not accept class objects.")
        except ValueError:
            pass

    async def test_override_request_expects_successful(self):
        class Request2(Request):
            @property
            def test(self):
                return "test"

        app = Vibora()
        app.request_class = Request2

        @app.route("/")
        async def home(request: Request2):
            return Response(request.test.encode())

        async with app.test_client() as client:
            response = await client.get("/")
            self.assertEqual(response.content, b"test")

    async def test_override_request_try_parent_one(self):
        class Request2(Request):
            @property
            def test(self):
                return "test"

        app = Vibora()
        app.request_class = Request2

        @app.route("/")
        async def home(request: Request):
            return Response(request.url)

        async with app.test_client() as client:
            response = await client.get("/")
            self.assertEqual(response.content, b"/")
