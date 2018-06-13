from asyncio import Task
from .router import Route


def get_component(type_):
    """

    :param type_:
    :return:
    """
    current_task = Task.current_task()
    return current_task.components.get(type_)


def get_current_route() -> Route:
    """

    :return:
    """
    return get_component(Route)
