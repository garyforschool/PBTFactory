import ast
import collections
import collections.abc
import itertools

import inspect

from typing import Any, Callable, Iterable, Mapping, Optional

from get_attribute_access_result import get_attribute_access_result
from get_comprehensive_dict_for_runtime_class import get_comprehensive_dict_for_runtime_class
from get_unwrapped_constructor import get_unwrapped_constructor
from scoped_evaluation_order_node_visitor import NodeProvidingScope, scoped_evaluation_order_node_visitor
from type_definitions import (
    RuntimeClass,
    UnwrappedRuntimeFunction,
    Function,
    FunctionDefinition,
    Instance,
    RuntimeTerm,
    UnboundMethod,
    BoundMethod
)
from unwrap import unwrap


def modified_handle_local_syntax_directed_typing_constraints(
    module_name: str,
    module_node: ast.Module,
    top_level_class_definitions_to_runtime_classes: Mapping[ast.ClassDef, RuntimeClass],
    unwrapped_runtime_functions_to_named_function_definitions: Mapping[UnwrappedRuntimeFunction, FunctionDefinition],
    named_function_definitions_to_unwrapped_runtime_functions: Mapping[FunctionDefinition, UnwrappedRuntimeFunction],
    node_to_definition_node_mapping: Mapping[ast.AST, ast.AST],
    get_runtime_terms_callback: Callable[[ast.AST], Iterable[RuntimeTerm]],
    update_runtime_terms_callback: Callable[[ast.AST, Iterable[RuntimeTerm]], Any],
):
    def get_runtime_terms_of_definition_node(node: ast.AST):
        nonlocal node_to_definition_node_mapping

        # Get the definition node, if it has one
        definition_node = node_to_definition_node_mapping.get(node, node)

        # Return the result of calling get_runtime_terms_callback on the definition node
        return get_runtime_terms_callback(definition_node)
    
    def update_runtime_terms_of_definition_node(node: ast.AST, runtime_terms: Iterable[RuntimeTerm]):
        nonlocal node_to_definition_node_mapping

        # Get the definition node, if it has one
        definition_node = node_to_definition_node_mapping.get(node, node)

        # Return the result of calling update_runtime_terms_callback on the definition node
        return update_runtime_terms_callback(definition_node, runtime_terms)

    def update_runtime_terms_of_definition_node_from_runtime_class(
        node: ast.AST,
        runtime_class: RuntimeClass
    ):
        update_runtime_terms_of_definition_node(node, {Instance(runtime_class)})
    
    def handle_local_syntax_directed_typing_constraints_callback(
        node: ast.AST,
        scope_stack: list[NodeProvidingScope]
    ):
        # Literals
        # ast.Constant(value)
        if isinstance(node, ast.Constant):
            # Set the current type variable to be an instance of `type(value)`
            update_runtime_terms_of_definition_node_from_runtime_class(node, type(node.value))
        # ast.JoinedStr(values)
        elif isinstance(node, ast.JoinedStr):
            # Set the current type variable to be an instance of `str`
            update_runtime_terms_of_definition_node_from_runtime_class(node, str)
        # ast.List(elts, ctx)
        elif isinstance(node, ast.List):
            # Set the current type variable to be an instance of `list`
            update_runtime_terms_of_definition_node_from_runtime_class(node, list)
        # ast.Tuple(elts, ctx)
        elif isinstance(node, ast.Tuple):
            # Set the current type variable to be an instance of `tuple`
            update_runtime_terms_of_definition_node_from_runtime_class(node, tuple)
        # ast.Set(elts)
        elif isinstance(node, ast.Set):
            # Set the current type variable to be an instance of `set`
            update_runtime_terms_of_definition_node_from_runtime_class(node, set)
        # ast.Dict(keys, values)
        elif isinstance(node, ast.Dict):
            # Set the current type variable to be an instance of `dict`
            update_runtime_terms_of_definition_node_from_runtime_class(node, dict)
        # Expressions
        # ast.Call(func, args, keywords, starargs, kwargs)
        # Output:
        # callee_module_name,callee_class_name,callee_function_name,caller_module_name,call_line
        elif isinstance(node, ast.Call):
            callee_module_name: Optional[str] = None
            callee_class_name: Optional[str] = None
            callee_function_name: Optional[str] = None
            caller_module_name: str = module_name
            caller_function_name: Optional[str] = getattr(scope_stack[-1], 'name', None) if scope_stack else None
            call_line: Optional[int] = getattr(node, 'lineno', None)
            caller_function_start: Optional[str] = getattr(scope_stack[-1], 'lineno', None) if scope_stack else None
            caller_function_end: Optional[str] = getattr(scope_stack[-1], 'end_lineno', None) if scope_stack else None

            # Handle function call for all runtime terms
            for runtime_term in get_runtime_terms_of_definition_node(node.func):
                if isinstance(runtime_term, RuntimeClass):
                    # Get the RuntimeClass's constructor
                    if (unwrapped_constructor := get_unwrapped_constructor(runtime_term)) in unwrapped_runtime_functions_to_named_function_definitions:
                        callee_module_name = runtime_term.__module__
                        callee_class_name = runtime_term.__name__
                        callee_function_name = unwrapped_constructor.__name__
                        callee_function = unwrapped_constructor

                
                    # Add an instance of the RuntimeClass to the node
                    update_runtime_terms_of_definition_node(
                        node,
                        {Instance(runtime_term)}
                    )

                elif isinstance(runtime_term, Function):
                    if isinstance(runtime_term, FunctionDefinition) and runtime_term in named_function_definitions_to_unwrapped_runtime_functions:
                        unwrapped_runtime_function = named_function_definitions_to_unwrapped_runtime_functions[runtime_term]
                        callee_module_name = unwrapped_runtime_function.__module__
                        callee_class_name = 'global'
                        callee_function_name = unwrapped_runtime_function.__name__
                        callee_function = unwrapped_runtime_function
                    elif isinstance(runtime_term, UnwrappedRuntimeFunction) and runtime_term in unwrapped_runtime_functions_to_named_function_definitions:
                        callee_module_name = runtime_term.__module__
                        callee_class_name = 'global'
                        callee_function_name = runtime_term.__name__
                        callee_function = runtime_term
                elif isinstance(runtime_term, UnboundMethod):
                    runtime_term_class = runtime_term.class_
                    function = runtime_term.function

                    if isinstance(function, FunctionDefinition) and function in named_function_definitions_to_unwrapped_runtime_functions:
                        unwrapped_runtime_function = named_function_definitions_to_unwrapped_runtime_functions[function]
                        callee_module_name = runtime_term_class.__module__
                        callee_class_name = runtime_term_class.__name__
                        callee_function_name = unwrapped_runtime_function.__name__
                        callee_function = unwrapped_runtime_function
                    elif isinstance(function, UnwrappedRuntimeFunction) and function in unwrapped_runtime_functions_to_named_function_definitions:
                        callee_module_name = runtime_term_class.__module__
                        callee_class_name = runtime_term_class.__name__
                        callee_function_name = function.__name__
                        callee_function = function
                elif isinstance(runtime_term, Instance):
                    runtime_term_class = runtime_term.class_
                    runtime_term_class_dict = get_comprehensive_dict_for_runtime_class(runtime_term_class)

                    if '__call__' in runtime_term_class_dict:
                        if (unwrapped_call := unwrap(runtime_term_class_dict['__call__'])) in unwrapped_runtime_functions_to_named_function_definitions:
                            callee_module_name = runtime_term_class.__module__
                            callee_class_name = runtime_term_class.__name__
                            callee_function_name = unwrapped_call.__name__
                            callee_function = unwrapped_call
                elif isinstance(runtime_term, BoundMethod):
                    runtime_term_instance_class = runtime_term.instance.class_
                    function = runtime_term.function

                    if isinstance(function, FunctionDefinition) and function in named_function_definitions_to_unwrapped_runtime_functions:
                        unwrapped_runtime_function = named_function_definitions_to_unwrapped_runtime_functions[function]
                        callee_module_name = runtime_term_instance_class.__module__
                        callee_class_name = runtime_term_instance_class.__name__
                        callee_function_name = unwrapped_runtime_function.__name__
                        callee_function = unwrapped_runtime_function
                    elif isinstance(function, UnwrappedRuntimeFunction) and function in unwrapped_runtime_functions_to_named_function_definitions:
                        callee_module_name = runtime_term_instance_class.__module__
                        callee_class_name = runtime_term_instance_class.__name__
                        callee_function_name = function.__name__
                        callee_function = function
                
                if callee_module_name and callee_class_name and callee_function_name:
                    source_lines, start_line = inspect.getsourcelines(callee_function)
                    end_line = start_line + len(source_lines) - 1
                    signature = inspect.signature(callee_function)
                    print(f'{callee_module_name},{callee_class_name},{callee_function_name},{start_line},{end_line},{caller_module_name},{caller_function_name},{call_line},{caller_function_start},{caller_function_end},"{signature}"')
        # ast.Attribute(value, attr, ctx)
        elif isinstance(node, ast.Attribute):
            # Get the runtime terms in `value`
            # Get the attribute access results
            attribute_access_results = set()
            for runtime_term in get_runtime_terms_of_definition_node(node.value):
                attribute_access_result = get_attribute_access_result(
                    runtime_term,
                    node.attr,
                    unwrapped_runtime_functions_to_named_function_definitions
                )

                if attribute_access_result is not None:
                    attribute_access_results.add(attribute_access_result)
            
            # Add the runtime terms to the node
            update_runtime_terms_of_definition_node(node, attribute_access_results)
        # ast.NamedExpr(target, value)
        elif isinstance(node, ast.NamedExpr):
            # Transfer runtime terms from `value` to `target`.
            update_runtime_terms_of_definition_node(
                node.target,
                get_runtime_terms_of_definition_node(
                    node.value
                )
            )
        # Comprehensions
        # ast.ListComp(elt, generators)
        elif isinstance(node, ast.ListComp):
            # Set the current type variable as equivalent to `list`.
            update_runtime_terms_of_definition_node_from_runtime_class(node, list)
        # ast.SetComp(elt, generators)
        elif isinstance(node, ast.SetComp):
            # Set the current type variable as equivalent to `set`.
            update_runtime_terms_of_definition_node_from_runtime_class(node, set)
        # ast.GeneratorExp(elt, generators)
        elif isinstance(node, ast.GeneratorExp):
            # Set the current type variable as equivalent to `collections.abc.Generator`.
            update_runtime_terms_of_definition_node_from_runtime_class(node, collections.abc.Generator)
        # ast.DictComp(key, value, generators)
        elif isinstance(node, ast.DictComp):
            # Set the current type variable as equivalent to `dict`.
            update_runtime_terms_of_definition_node_from_runtime_class(node, dict)
        # Statements
        # ast.Assign(targets, value, type_comment)
        elif isinstance(node, ast.Assign):
            for (value, target) in itertools.pairwise(
                reversed(node.targets + [node.value])
            ):
                # Transfer runtime terms from `value` to `target`.
                update_runtime_terms_of_definition_node(
                    target,
                    get_runtime_terms_of_definition_node(
                        value
                    )
                )
        # ast.AnnAssign(target, annotation, value, simple)
        elif isinstance(node, ast.AnnAssign):
            if node.value is not None:
                # Transfer runtime terms from `value` to `target`.
                update_runtime_terms_of_definition_node(
                    node.target,
                    get_runtime_terms_of_definition_node(
                        node.value
                    )
                )
        # Function Definition
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            # Add runtime terms
            update_runtime_terms_of_definition_node(node, {node})
        # ast.ClassDef(name, bases, keywords, body, decorator_list, type_params)
        elif isinstance(node, ast.ClassDef):
            if node in top_level_class_definitions_to_runtime_classes:
                runtime_class = top_level_class_definitions_to_runtime_classes[node]

                # Add runtime terms
                update_runtime_terms_of_definition_node(node, {runtime_class})

    return scoped_evaluation_order_node_visitor(
        module_node,
        handle_local_syntax_directed_typing_constraints_callback
    )
