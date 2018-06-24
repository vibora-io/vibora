from collections import Callable
from .nodes import BlockNode, MacroNode, IncludeNode, Node


def find_all(search_function, node):
    elements = []
    for child in node.children:
        if search_function(child):
            elements.append(child)
        if child.children:
            find_all(search_function, child)
    return elements


def replace_on_tree(look_for: Callable, new_node: Callable, current_node: Node):
    """

    :param new_node:
    :param look_for:
    :param current_node:
    :return:
    """
    pending_replace = []
    for index, child in enumerate(current_node.children):
        if look_for(child):
            pending_replace.append(index)
    for index in pending_replace:
        current_node.children[index] = new_node(current_node.children[index])
    for index, child in enumerate(current_node.children):
        if index not in pending_replace:
            replace_on_tree(look_for, new_node, child)


def replace_all(search_function, replace_with, node):
    new_children = []
    for child in node.children:
        if search_function(child):
            new_children.append(replace_with)
        else:
            new_children.append(child)
        if child.children:
            replace_all(search_function, replace_with, child)
    node.children = new_children


def raise_nodes(match, node, inner=False):
    nodes_to_be_raised = []
    nodes_to_be_deleted = []
    for index, child in enumerate(node.children):
        if match(child):
            nodes_to_be_raised.append(child)
            nodes_to_be_deleted.append(index)
        if child.children:
            for inner_child in child.children:
                nodes = raise_nodes(match, inner_child, inner=True)
                nodes_to_be_raised += nodes
    for index in sorted(nodes_to_be_deleted, reverse=True):
        del node.children[index]
    if inner is False:
        node.children = nodes_to_be_raised + node.children
    else:
        return nodes_to_be_raised


def merge(a, b):
    new_ast = a.ast

    # Replacing blocks.
    new_blocks = find_all(lambda x: isinstance(x, BlockNode), b.ast)
    for block in new_blocks:
        replace_all(
            lambda x: isinstance(x, BlockNode) and x.name == block.name, block, new_ast
        )

    # Preserving macros.
    macros = find_all(lambda x: isinstance(x, MacroNode), b.ast)
    for macro in macros:
        a.ast.children.append(macro)

    return new_ast


def resolve_include_nodes(engine, nodes: list) -> list:
    relationships = []
    for index, node in enumerate(nodes):
        if isinstance(node, IncludeNode):
            target = engine.get_template(node.target)
            relationships.append(target)
            engine.prepare_template(target)
            nodes[index] = target.ast
        elif node.children:
            inner_relationships = resolve_include_nodes(engine, node.children)
            relationships += inner_relationships
    return relationships
