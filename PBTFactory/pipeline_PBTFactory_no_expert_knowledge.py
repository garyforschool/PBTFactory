import json
import os
import textwrap

from PBTFactory.message import MessageManager, count_code, find_code
from PBTFactory.pipeline_PBTFactory import *


def create_ask_property_prompt(
    function_name: str, function: str, test: str, class_structure: str
) -> tuple:
    if function:
        function = f"Function:\n```python\n{function}\n```\n\n"
    if test:
        test = f"Test:\n```python\n{test}\n```\n\n"
    if class_structure:
        class_structure = f"Class Structure:\n```python\n{class_structure}\n```\n\n"

    template = (
        textwrap.dedent(
            """\
        You are going to write property based test for `{}`.

        {}{}{}

        What are some properties you would like to test for this function? Max 3 properties.
        return a list of properties in the json format of"""
        ).format(function_name, function, class_structure, test)
        + ' ```[\{ "name": _, "explain": _\}, \{...\}]```\n'
    )
    return template


class pipeline_PBTFactory_no_expert_knowledge(pipeline_PBTFactory):

    def get_property_list_from_msg(self, msg):
        if count_code(msg) == 0:
            return []
        else:
            code = find_code(msg)
            try:
                properties = json.loads(code)
            except json.JSONDecodeError:
                return []
            result = []
            for prop in properties:
                r = {}
                if "name" in prop or "Name" in prop:
                    r["name"] = prop.get("name", prop.get("Name"))
                else:
                    continue
                if "explain" in prop or "Explain" in prop:
                    r["explain"] = prop.get("explain", prop.get("Explain"))
                else:
                    continue
                result.append(r)
            return result

    def get_property_list(self, code_explanation, retry=3):
        mm = MessageManager()
        mm.add_user_message(
            create_ask_property_prompt(
                self.cut_data.cut.entry_point,
                self.cut_data.cut.function_body,
                self.cut_data.cut.test,
                self.cut_data.cut.class_structure,
            )
        )

        msg = self.chat.ask(mm, "ask_property_list")
        mm.add_assistant_message(msg)

        properties = self.get_property_list_from_msg(msg)

        if not properties:
            mm.add_user_message(
                "The input is not a valid json format. Please return in json."
            )
            msg = self.chat.ask(mm, "ask_property_list_json")
            properties = self.get_property_list_from_msg(msg)
            if not properties and retry > 0:
                return self.get_property_list(code_explanation, retry - 1)
        return properties
