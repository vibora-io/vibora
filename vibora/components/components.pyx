from typing import Callable, Type, get_type_hints
from inspect import isclass
from ..exceptions import MissingComponent


class Component:

    __slots__ = ('builder', 'cache_enabled', 'cache')

    def __init__(self, builder: Callable = None, cache=False, prebuilt=None):
        try:
            if builder:
                self.type = get_type_hints(builder)['return']
            elif not prebuilt:
                raise ValueError('You need to pass either builder or prebuilt param.')
            self.builder = builder
            self.cache_enabled = cache
            self.cache = prebuilt
        except KeyError:
            raise ValueError(f'Please type hint the return type of your function. ({builder})')

    def build(self):
        """

        :return:
        """
        if self.cache is not None:
            return self.cache
        if self.cache_enabled:
            self.cache = self.builder()
            return self.cache
        return self.builder()


cdef class ComponentsEngine:
    def __init__(self):
        self.index = {}
        self.ephemeral_index = {}

    def __getitem__(self, item):
        return self.get(item)

    def add(self, *components, bint ephemeral=False):
        """

        :param ephemeral:
        :param components:
        :return:
        """
        cdef dict index = self.index
        if ephemeral is True:
            index = self.ephemeral_index
        for component in components:
            if isinstance(component, Component):
                if component.type in self.index:
                    raise ValueError('There is already a component that provides this type. '
                                     'You probably should create a subtype.')
                index[component.type] = component
            elif isclass(component):
                raise ValueError("You shouldn't add class objects to ComponentsEngine. "
                                 "Try an instance of this class or wrap it around a Component object.")
            else:
                type_ = type(component)
                if type_ in self.index:
                    raise ValueError('There is already a component that provides this type. '
                                     'You probably should create a subtype.')
                index[type_] = Component(prebuilt=component)

    @staticmethod
    def search_type(dict index, object required_type):
        element = None
        for key, value in index.items():
            if issubclass(key, required_type):
                if element is None:
                    element = key
                else:
                    raise ValueError("Vibora can't decide which component do you want, "
                                     f"because there at least two types who are a subclass of {required_type}")
        return element

    def get(self, required_type: Type):
        """

        :param required_type:
        :return:
        """
        # Ephemeral index is where Request/Route and other internal framework components are stored.
        # They are reset every request/response cycle so they are keep separated
        # to keep recycling faster.
        if required_type in self.ephemeral_index:
            return self.ephemeral_index[required_type]
        try:
            return self.index[required_type].build()
        except KeyError:
            key = self.search_type(self.index, required_type)
            second_key = self.search_type(self.ephemeral_index, required_type)
            if key is not None and second_key is not None:
                raise MissingComponent("Vibora can't decide which component do you want, "
                                       f"because there at least two types who are a subclass of {required_type}",
                                       component=required_type)
            elif key is not None:
                return self.index[key].build()
            elif second_key is not None:
                return self.ephemeral_index[second_key]
        raise MissingComponent(f'ComponentsEngine miss a component of type: {required_type}', component=required_type)

    cpdef ComponentsEngine clone(self):
        """

        :return:
        """
        new = ComponentsEngine()
        new.index = self.index.copy()
        return new

    cdef void reset(self):
        """
        
        :return: 
        """
        self.ephemeral_index.clear()
