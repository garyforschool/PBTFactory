import json
import re


class MessageManager:
    def __init__(self) -> None:
        self.messages = []

    def add_user_message(self, message):
        if not message.endswith("\n"):
            message += "\n"
        self.messages.append({"role": "user", "content": message})

    def add_assistant_message(self, message):
        self.messages.append({"role": "assistant", "content": message})

    def replace_content(self, content, replaceby):
        for m in self.messages:
            m["content"] = m["content"].replace(content, replaceby)

    def __str__(self) -> str:
        return "\n".join([f"{m['role']}:\n{m['content']}\n" for m in self.messages])

    def copy(self):
        new = MessageManager()
        new.messages = self.messages.copy()
        return new

    def save(self, filename):
        with open(filename, "w") as f:
            f.write(str(self))

        with open(filename + ".json", "w") as f:
            json.dump(self.messages, f, indent=4)

    def remove_last(self) -> dict:
        return self.messages.pop()


def get_code_blocks(msg):
    try:
        code_search = re.findall(r"```(.*?)```", msg, re.DOTALL)
    except re.error:
        code_search = []
    return code_search


def count_code(msg):
    return len(get_code_blocks(msg))


def find_code(msg):
    code_search = get_code_blocks(msg)
    if len(code_search) > 1:
        pass
        # logging.warning(f"More than one code block found.\n{msg}")

    longest_code = ""
    max_len = 0
    for code in code_search:  # Find the longest code block
        code = code.strip()
        if code.startswith("python"):
            code = code[len("python") :].strip()
        elif code.startswith("json"):
            code = code[len("json") :].strip()
        if len(code) > max_len:
            longest_code = code
            max_len = len(code)
    return longest_code


def replace_code(msg, code):
    try:
        result = re.sub(
            r"```.*```", "```\n||-NOT_POSSIBLE-||\n```", msg, flags=re.DOTALL
        )  # To make sure special characters such as \n \t, are not replaced
        result = result.replace("||-NOT_POSSIBLE-||", code)
    except re.error:
        result = msg
    return result
