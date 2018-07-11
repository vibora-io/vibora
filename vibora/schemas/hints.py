from .messages import EnglishLanguage
from ..request import Request


class Schema:

    _fields = []

    def __init__(self, silent: bool = False):
        """

        :param silent:
        """
        pass

    @classmethod
    async def load(
        cls, values: dict, language: dict = EnglishLanguage, context: dict = None
    ) -> "Schema":
        """

        :param context:
        :param values:
        :param language:
        :return:
        """
        pass

    @classmethod
    async def load_form(
        cls, request: Request, language: dict = EnglishLanguage, context: dict = None
    ) -> "Schema":
        """

        :param context:
        :param request:
        :param language:
        :return:
        """
        pass

    @classmethod
    async def load_json(
        cls, request: Request, language: dict = EnglishLanguage, context: dict = None
    ) -> "Schema":
        """

        :param context:
        :param request:
        :param language:
        :return:
        """
        pass
