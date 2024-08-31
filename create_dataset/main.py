import ast
import importlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import time

import astor
import numpy as np
import pandas as pd


project_root = 'dataset/flutils/flutils'
out_path = 'dataset/flutils/test_data'
tmp_data_path = 'calles.csv'

def remove_comments(source):
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):
                if ast.get_docstring(node):
                    node.body = node.body[1:]
                if not node.body:
                    node.body = [ast.Pass()]
        result = astor.to_source(tree)
    except:
        result = source
    return result


for root, dirs, files in os.walk(project_root):
    for file in files:
        if file.endswith('.py'):
            try:
                with open(os.path.join(root, file), 'r') as f:
                    source = f.read()
                new_source = remove_comments(source)
                with open(os.path.join(root, file), 'w') as f:
                    f.write(new_source)
            except:
                print(f'Error in {os.path.join(root, file)}')

subprocess.call(f"black {project_root}", shell=True)
time.sleep(2)

if os.path.exists(tmp_data_path):
    os.remove(tmp_data_path)

subprocess.call(f"python find_usages -s {project_root} > {tmp_data_path} 2>/dev/null", shell=True)


sys.path.append(project_root)

def collect_code(file_name, start, end):
    start = int(start)
    end = int(end)
    with open(os.path.join(project_root, file_name)) as f:
        lines = f.readlines()
    while start > 1 and lines[start-1].strip():
        start -= 1
    return ''.join(lines[start-1:end]).strip()


df = pd.read_csv(tmp_data_path, header=None, on_bad_lines='warn')
df = df.replace({np.nan: None})
list_of_lists = df.values.tolist()
functions = []
class Function:
    def __init__(self, package, classname, name, signature, startline, endline):
        self.package = package
        self.classname = classname
        self.name = name
        self.signature = signature
        self.startline = startline
        self.endline = endline
        module = importlib.import_module(package)
        self.filename = os.path.relpath(inspect.getfile(module), project_root)
        self.full_code = collect_code(self.filename, 1, 1000000)

        self.code = collect_code(self.filename, startline, endline)

    def __str__(self):
        return f'{self.package}.{self.classname}.{self.name}'
    
    def __eq__(self, other):
        if not isinstance(other, Function):
            return False
        return self.package == other.package and self.classname == other.classname and self.name == other.name

for row in list_of_lists:
    try:
        if (not 'tests' in row[0]) and (not 'init' in row[2]) and ('tests' in row[5]):
            if row[3] is None or row[8] is None:
                continue
            function = Function(row[0], row[1], row[2], row[10], row[3], row[4])
            test_function = Function(row[5], None, row[6], None, row[8], row[9])
            added = False
            for index in range(len(functions)):
                if functions[index][0] == function:
                    added = True
                    if test_function not in functions[index][1]:
                        functions[index][1].append(test_function)
                    break
            if not added:
                functions.append([function, [test_function]])
    except (ImportError, UnicodeError):
        pass
        # print(row)


shutil.rmtree(out_path, ignore_errors=True)
if len(functions) == 0:
    print('No functions found')
    sys.exit(0)
for function in functions[:]:
    os.makedirs(os.path.join(out_path, function[0].__str__()))
    with open(os.path.join(out_path, function[0].__str__(), 'code.py'), 'w') as f:
        f.write(function[0].full_code)
    test_codes = []
    for test_function in function[1]:
        if test_function.code not in test_codes:
            test_codes.append(test_function.code)
    with open(os.path.join(out_path, function[0].__str__(), 'test_code.py'), 'w') as f:
        f.write("\n\n".join(test_codes))

    setup_data = {"name": function[0].name, 
                  "signature": f"def {function[0].name}{function[0].signature}", 
                  "filepath": function[0].filename, 
                  "package": function[0].package, "classname": function[0].classname,
                  "startline": function[0].startline, "endline": function[0].endline}
    json.dump(setup_data, open(os.path.join(out_path, function[0].__str__(), 'setup_data.json'), 'w'))
