# import argparse
import builtins
import collections
import importlib
import itertools
import json
import logging
import os
import os.path
import sys
import types
import typing
import argparse

from ast import AST
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from ast_node_namespace_trie import get_ast_node_namespace_trie, search_ast_node_namespace_trie
from get_definitions_to_runtime_terms_mappings import get_definitions_to_runtime_terms_mappings
from get_module_names_to_imported_names_to_runtime_objects import get_module_names_to_imported_names_to_runtime_objects
from get_use_define_mapping import get_use_define_mapping
from modified_handle_local_syntax_directed_typing_constraints import modified_handle_local_syntax_directed_typing_constraints
from static_import_analysis import do_static_import_analysis
from trie import search
from type_definitions import *
from unwrap import unwrap


if __name__ == '__main__':


# def run(path_to_target: str, path_to_output: str):
    # import sys
    # f = open(path_to_output, 'w')
    # sys.stdout = f
    # Set up logging
    # https://stackoverflow.com/questions/10973362/python-logging-function-name-file-name-line-number-using-a-single-file
    FORMAT = '[%(asctime)s %(filename)s %(funcName)s():%(lineno)s]%(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.WARNING)

    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--module-search-path', type=str, required=True, help='Module search path')
    args = parser.parse_args()

    # Search modules

    module_search_absolute_path: str = os.path.abspath(args.module_search_path)
    # module_search_absolute_path: str = os.path.abspath(path_to_target)
    (
        module_name_to_file_path_dict,
        module_name_to_function_name_to_parameter_name_list_dict,
        module_name_to_class_name_to_method_name_to_parameter_name_list_dict,
        module_name_to_import_tuple_set_dict,
        module_name_to_import_from_tuple_set_dict
    ) = do_static_import_analysis(module_search_absolute_path)

    # Import modules

    module_name_to_module_node = {}
    module_name_to_module = {}

    sys.path.insert(0, module_search_absolute_path)

    for module_name, file_path in module_name_to_file_path_dict.items():
        if file_path.endswith('setup.py') or file_path.endswith('__main__.py'):
            continue
        try:
            with open(file_path, 'r') as fp:
                code = fp.read()
                module_node = ast.parse(code)
            module = importlib.import_module(module_name)
            module_name_to_module_node[module_name] = module_node
            module_name_to_module[module_name] = module
        except (ImportError, UnicodeError):
            logging.exception('Failed to import module %s', module_name)

    module_names = list(module_name_to_module_node.keys())
    module_nodes = list(module_name_to_module_node.values())
    modules = list(module_name_to_module.values())
    # Get information from all modules

    module_names_to_imported_names_to_runtime_objects = get_module_names_to_imported_names_to_runtime_objects(
        module_name_to_import_tuple_set_dict,
        module_name_to_import_from_tuple_set_dict,
        module_name_to_module
    )

    (
        top_level_class_definitions_to_runtime_classes,
        unwrapped_runtime_functions_to_named_function_definitions
    ) = get_definitions_to_runtime_terms_mappings(
        module_names,
        modules,
        module_nodes
    )

    named_function_definitions_to_unwrapped_runtime_functions = {
        named_function_definition: unwrapped_runtime_function
        for unwrapped_runtime_function, named_function_definition
        in unwrapped_runtime_functions_to_named_function_definitions.items()
    }

    # STATEFUL SECTION

    node_runtime_terms = {}

    def get_runtime_terms(node_: ast.AST):
        return node_runtime_terms.get(node_, set())

    def update_runtime_terms(node_: ast.AST, runtime_terms: typing.Iterable[RuntimeTerm]):
        node_runtime_terms.setdefault(node_, set()).update(runtime_terms)

    # Handle each module

    for module_name, module_node in module_name_to_module_node.items():
        # Initialize dummy definition nodes with builtins and imports
        names_to_dummy_definition_nodes = {}

        for key, value in builtins.__dict__.items():
            name = key
            unwrapped_value = unwrap(value)
            if (not name.startswith('_')) and isinstance(unwrapped_value, (RuntimeClass, UnwrappedRuntimeFunction)):
                dummy_definition_node = ast.AST()
                setattr(dummy_definition_node, 'id', name)

                names_to_dummy_definition_nodes[name] = dummy_definition_node

                if isinstance(unwrapped_value, RuntimeClass):
                    update_runtime_terms(dummy_definition_node, {unwrapped_value})
                elif isinstance(unwrapped_value, UnwrappedRuntimeFunction):
                    update_runtime_terms(dummy_definition_node, {runtime_term_of_unwrapped_runtime_function(unwrapped_value)})

        for value in (True, False, Ellipsis, None, NotImplemented):
            name = str(value)

            dummy_definition_node = ast.AST()
            setattr(dummy_definition_node, 'id', name)

            names_to_dummy_definition_nodes[name] = dummy_definition_node
            update_runtime_terms(dummy_definition_node, {Instance(type(value))})

        imported_names_to_runtime_objects = module_names_to_imported_names_to_runtime_objects.get(module_name, {})
        for imported_name, runtime_object in imported_names_to_runtime_objects.items():
            unwrapped_runtime_object = unwrap(runtime_object)
            runtime_term: typing.Optional[RuntimeTerm] = None

            if isinstance(unwrapped_runtime_object, Module):
                runtime_term = unwrapped_runtime_object
            elif isinstance(unwrapped_runtime_object, RuntimeClass):
                runtime_term = unwrapped_runtime_object
            elif isinstance(unwrapped_runtime_object, UnwrappedRuntimeFunction):
                processed_unwrapped_runtime_object = runtime_term_of_unwrapped_runtime_function(unwrapped_runtime_object)

                runtime_term = unwrapped_runtime_functions_to_named_function_definitions.get(
                    processed_unwrapped_runtime_object,
                    processed_unwrapped_runtime_object
                )
            
            if runtime_term is not None:
                dummy_definition_node = ast.AST()
                setattr(dummy_definition_node, 'id', imported_name)

                names_to_dummy_definition_nodes[imported_name] = dummy_definition_node
                update_runtime_terms(dummy_definition_node, {runtime_term})
            else:
                logging.error(
                    'Cannot match imported name %s in module %s with unwrapped runtime object %s to a runtime term!',
                    imported_name, module_name, unwrapped_runtime_object
                )

        
        # Add dummy nodes for all classes defined within the file
        for key, value in module_name_to_module[module_name].__dict__.items():
            name = key
            unwrapped_value = unwrap(value)
            if isinstance(unwrapped_value, type) and unwrapped_value.__module__ == module_name:
                dummy_definition_node = ast.AST()
                setattr(dummy_definition_node, 'id', name)

                names_to_dummy_definition_nodes[name] = dummy_definition_node

                update_runtime_terms(dummy_definition_node, {unwrapped_value})
        
        
        use_define_mapping = get_use_define_mapping(
            module_node,
            names_to_dummy_definition_nodes
        )

        node_to_definition_node_mapping = {
            node: definition_node
            for definition_node, nodes in use_define_mapping.itersets()
            for node in nodes
        }

        modified_handle_local_syntax_directed_typing_constraints(
            module_name,
            module_node,
            top_level_class_definitions_to_runtime_classes,
            unwrapped_runtime_functions_to_named_function_definitions,
            named_function_definitions_to_unwrapped_runtime_functions,
            node_to_definition_node_mapping,
            get_runtime_terms,
            update_runtime_terms,
        )
