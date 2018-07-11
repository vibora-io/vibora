from vibora.tests import TestSuite
from vibora.blueprints import Blueprint, Response
from vibora.router import RouterStrategy
from vibora import Vibora


class BlueprintsTestCase(TestSuite):
    def setUp(self):
        self.app = Vibora(router_strategy=RouterStrategy.STRICT)

    async def test_simple_add_blueprint__expects_added(self):
        b1 = Blueprint()

        @b1.route("/")
        async def home():
            return Response(b"123")

        self.app.add_blueprint(b1)
        async with self.app.test_client() as client:
            response = await client.request("/")
            self.assertEqual(response.content, b"123")

    async def test_simple_add_blueprint_with_prefix_expects_added(self):
        b1 = Blueprint()

        @b1.route("/")
        async def home():
            return Response(b"123")

        self.app.add_blueprint(b1, prefixes={"home": "/home"})
        async with self.app.test_client() as client:
            response = await client.request("/home/")
            self.assertEqual(response.content, b"123")

    async def test_simple_add_nested_blueprints(self):
        b1 = Blueprint()
        b2 = Blueprint()

        @b2.route("/123")
        async def home():
            return Response(b"123")

        b1.add_blueprint(b2)
        self.app.add_blueprint(b1)
        async with self.app.test_client() as client:
            response = await client.request("/123")
            self.assertEqual(response.content, b"123")

    async def test_simple_add_nested_blueprints_with_prefixes(self):
        b1 = Blueprint()
        b2 = Blueprint()

        @b2.route("/123")
        async def home():
            return Response(b"123")

        b1.add_blueprint(b2, prefixes={"a": "/a", "b": "/b"})
        self.app.add_blueprint(b1, prefixes={"a": "/a", "b": "/b"})
        async with self.app.test_client() as client:
            response = await client.request("/a/a/123")
            self.assertEqual(response.content, b"123")
            response = await self.app.test_client().request("/b/b/123")
            self.assertEqual(response.content, b"123")

    # def test_routes_added_to_router_with_non_empty_pattern(self):
    #     b1 = Blueprint()
    #     new_route = Route('/', lambda: 'Hello', methods=['GET'])
    #     b1.add_route(new_route)
    #     v = Vibora(router_strategy=RouteStrategy.STRICT)
    #     prefixes = {'': '/v1'}
    #     v.add_blueprint(b1, prefixes=prefixes)
    #     for route in v.router.routes['GET']:
    #         if route.pattern == '/v1/':
    #             return
    #     self.fail('Failed to find Route.')
    #
    # def test_nested_blueprints_expects_correct_pattern(self):
    #     b1 = Blueprint()
    #     b2 = Blueprint()
    #     b1.add_blueprint(b2, prefixes={'b2': '/b2'})
    #     new_route = Route('/', lambda: 'Hello', methods=['GET'], name='hello')
    #     b2.add_route(new_route)
    #     v = Vibora(router_strategy=RouteStrategy.STRICT)
    #     v.add_blueprint(b1, prefixes={'': ''})
    #     for route in v.router.routes['GET']:
    #         if route.pattern == '/b2/':
    #             return
    #     self.fail('Failed to find Route.')
    #
    # def test_three_nested_blueprints_expects_correct_pattern(self):
    #     b1 = Blueprint()
    #     b2 = Blueprint()
    #     b3 = Blueprint()
    #     b1.add_blueprint(b2, prefixes={'b2': '/b2'})
    #     b2.add_blueprint(b3, prefixes={'b3': '/b3'})
    #     new_route = Route('/', lambda: 'Hello', methods=['GET'])
    #     b3.add_route(new_route)
    #     v = Vibora(router_strategy=RouteStrategy.STRICT)
    #     v.add_blueprint(b1, prefixes={'': '/b1'})
    #     for route in v.router.routes['GET']:
    #         if route.pattern == '/b1/b2/b3/':
    #             return
    #     self.fail('Failed to find Route.')
    #
    # def test_reverse_index_nested_blueprints(self):
    #     b1 = Blueprint()
    #     b2 = Blueprint()
    #     b3 = Blueprint()
    #     b1.add_blueprint(b2, prefixes={'b2': '/b2'})
    #     b2.add_blueprint(b3, prefixes={'b3': '/b3'})
    #     new_route = Route('/', lambda: 'Hello', methods=['GET'], name='hello')
    #     b3.add_route(new_route)
    #     v = Vibora(router_strategy=RouteStrategy.STRICT)
    #     v.add_blueprint(b1, prefixes={'': '/b1'})
    #     self.assertTrue(
    #         'b2:b3.hello' in v.router.reverse_index
    #     )
    #
    # def test_reverse_index_nested_blueprints_non_empty(self):
    #     b1 = Blueprint()
    #     b2 = Blueprint()
    #     b3 = Blueprint()
    #     b1.add_blueprint(b2, prefixes={'b2': '/b2'})
    #     b2.add_blueprint(b3, prefixes={'b3': '/b3'})
    #     new_route = Route('/', lambda: 'Hello', methods=['GET'], name='hello')
    #     b3.add_route(new_route)
    #     v = Vibora(router_strategy=RouteStrategy.STRICT)
    #     v.add_blueprint(b1, prefixes={'b1': '/b1'})
    #     self.assertTrue(
    #         'b1:b2:b3.hello' in v.router.reverse_index
    #     )
