from vibora import Vibora, Request
from vibora.responses import Response, JsonResponse
from vibora.blueprints import Blueprint
from vibora.tests import TestSuite


class ExceptionsTestCase(TestSuite):
    def setUp(self):
        self.app = Vibora()

    async def test_simple_exception_expects_handled(self):
        @self.app.route("/")
        async def home():
            raise Exception("Vibora ;)")

        @self.app.handle(Exception)
        async def handle_errors():
            return Response(b"Catch!", status_code=500)

        async with self.app.test_client() as client:
            response = await client.get("/")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Catch!")

    async def test_simple_exception_with_default_handler(self):
        @self.app.route("/")
        async def handle_errors():
            raise Exception("Vibora ;)")

        response = await self.app.test_client().request("/")
        self.assertEqual(response.status_code, 500)

    async def test_different_exception__expects_not_handled(self):
        class NewException(Exception):
            pass

        @self.app.route("/")
        async def handle_errors():
            raise Exception("Vibora ;)")

        @self.app.handle(NewException)
        async def handle_errors2():
            return Response(b"Catch!", status_code=500)

        response = await self.app.test_client().request("/")
        self.assertEqual(response.status_code, 500)
        self.assertNotEqual(response.content, b"Catch!")

    async def test_subclassed_exception__expects_handled(self):
        class ParentException(Exception):
            pass

        class ChildException(ParentException):
            pass

        @self.app.route("/")
        async def handle_errors():
            raise ChildException("Vibora ;)")

        @self.app.handle(ParentException)
        async def handle_errors2():
            return Response(b"Catch!", status_code=500)

        response = await self.app.test_client().request("/")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Catch!")

    async def test_specific_priority_exception_catch_expects_handled(self):
        class ParentException(Exception):
            pass

        class ChildException(ParentException):
            pass

        @self.app.route("/")
        async def handle_errors():
            raise ChildException("Vibora ;)")

        @self.app.handle(ParentException)
        async def handle_errors2():
            return Response(b"Parent!", status_code=500)

        @self.app.handle(ChildException)
        async def handle_errors3():
            return Response(b"Child!", status_code=500)

        response = await self.app.test_client().request("/")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Child!")

    async def test_harder_subclass_exception_catch_expects_handled(self):
        class ExceptionA(Exception):
            pass

        class ExceptionB(ExceptionA):
            pass

        class ExceptionC(ExceptionB):
            pass

        @self.app.route("/")
        async def handle_errors():
            raise ExceptionC("Vibora ;)")

        @self.app.handle(ExceptionA)
        async def handle_errors2():
            return Response(b"Wrong!", status_code=500)

        @self.app.handle(ExceptionB)
        async def handle_errors3():
            return Response(b"Correct!", status_code=500)

        response = await self.app.test_client().request("/")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Correct!")

    async def test_blueprint_exception_propagation(self):
        b1 = Blueprint()

        class ExceptionA(Exception):
            pass

        class ExceptionB(ExceptionA):
            pass

        class ExceptionC(ExceptionB):
            pass

        @b1.route("/")
        async def handle_errors():
            raise ExceptionC("Vibora ;)")

        @self.app.handle(ExceptionA)
        async def handle_errors2():
            return Response(b"Wrong!", status_code=500)

        @self.app.handle(ExceptionB)
        async def handle_errors3():
            return Response(b"Correct!", status_code=500)

        self.app.add_blueprint(b1, prefixes={"": ""})

        response = await self.app.test_client().request("/")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Correct!")

    async def test_nested_blueprint_exception_propagation(self):
        b1 = Blueprint()
        b2 = Blueprint()

        class ExceptionA(Exception):
            pass

        @b2.route("/")
        async def handle_errors():
            raise ExceptionA("Vibora ;)")

        @self.app.handle(ExceptionA)
        async def handle_errors2():
            return Response(b"Wrong!", status_code=500)

        b1.add_blueprint(b2, prefixes={"": ""})
        self.app.add_blueprint(b1, prefixes={"": ""})

        response = await self.app.test_client().request("/")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Wrong!")

    async def test_nested_blueprint_exception_propagation_conflicts(self):
        b1 = Blueprint()
        b2 = Blueprint()

        class ExceptionA(Exception):
            pass

        @b2.route("/")
        async def handle_errors():
            raise ExceptionA("Vibora ;)")

        @self.app.handle(ExceptionA)
        async def handle_errors2():
            return Response(b"Wrong!", status_code=500)

        b1.add_blueprint(b2, prefixes={"": ""})
        self.app.add_blueprint(b1, prefixes={"": ""})

        response = await self.app.test_client().request("/")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Wrong!")

    async def test_multiple_exceptions_at_a_single_handle(self):
        b1 = Blueprint()
        b2 = Blueprint()

        class ExceptionA(Exception):
            pass

        @b2.route("/")
        async def handle_errors():
            raise ExceptionA("Vibora ;)")

        @self.app.handle((IOError, ExceptionA))
        async def handle_errors2():
            return Response(b"Correct!", status_code=500)

        b1.add_blueprint(b2, prefixes={"": ""})
        self.app.add_blueprint(b1, prefixes={"": ""})

        response = await self.app.test_client().request("/")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Correct!")

    async def test_exception_flow_expects_parent_response(self):
        @self.app.route("/")
        async def handle_errors():
            raise IOError("Vibora ;)")

        @self.app.handle(IOError)
        async def handle_io(request: Request):
            request.context["called"] = True

        @self.app.handle(Exception)
        async def handle_errors2(request: Request):
            return JsonResponse({"called": request.context.get("called")}, status_code=500)

        async with self.app.test_client() as client:
            response = await client.request("/")

        self.assertEqual(response.status_code, 500)
        self.assertDictEqual(response.json(), {"called": True})
