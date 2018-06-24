from typing import Type
from asyncio import Task


def get_component(type_: Type):
    """
    Get a component based .
    :param type_:
    :return:
    """
    current_task = Task.current_task()
    return current_task.components.get(type_)
