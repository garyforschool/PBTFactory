import ast

import astor


class ReplaceFuncImplWithPass(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        node.body = [ast.Pass()]
        return node


def extract_class_nodes(code, class_name):
    tree = ast.parse(code)
    class_nodes = []

    class ClassVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            if node.name == class_name:
                class_nodes.append(node)
            self.generic_visit(node)

    visitor = ClassVisitor()
    visitor.visit(tree)
    return class_nodes


def get_class_structure(code, class_name):
    tree = ast.parse(code)
    tree = extract_class_nodes(code, class_name)[0]
    transformer = ReplaceFuncImplWithPass()
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    return transformed_tree
