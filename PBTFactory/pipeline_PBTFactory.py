import os
import textwrap

from PBTFactory.chat import Chat
from PBTFactory.cut_data import CUT_data
from PBTFactory.eval_code import run_code, run_pytest
from PBTFactory.message import MessageManager, count_code, find_code, replace_code
from PBTFactory.pipeline import Pipeline
from PBTFactory.request_manager import RequestType

suffix = "The function may not have exact property. However, as long as the function is close to the property, it is acceptable or it is meaning to check. You need to say yes and reason about the function and the property."
# Some copyed from F# by ScottW.
property_Symmetry = {
    "name": "Round-tripping",
    "explain": "Round-tripping in property-based testing means that if an operation has a symmetric counterpart, applying the operation in both directions should yield consistent results.",
}
property_Alternatives = {
    "name": "Alternatives",
    "explain": "Alternatives refer to the concept that different ways of achieving the same outcome should produce identical results. In property-based testing, this means verifying that multiple methods or algorithms that are supposed to solve the same problem yield the same results for the same inputs. It is meaningful to compare the results of different methods. You need to first understand what the function is doing, then come up with alternative ways to achieve the same result.",
}
property_Induction = {
    "name": "Induction",
    "explain": "Induction in property-based testing is used to test properties that hold true for an entire range of inputs by proving they hold for a base case and then for any incrementally larger case. This is similar to mathematical induction and is often used to verify recursive functions.",
}
property_Idempotence = {
    "name": "Idempotence",
    "explain": "Idempotence in property-based testing means that applying an operation twice is the same as doing it once. For example, if a function f is idempotent, then f(f(x)) should equal f(x). Be sure to check parameters meaning and return meaning before applying.",
}
property_Invariants = {
    "name": "Invariants/Some things never change",
    "explain": "Invariants are properties or conditions that remain unchanged throughout the execution of a program or a sequence of operations. In property-based testing, invariants are used to ensure that certain properties hold true before and after operations.",
}
property_Property_Constraints = {
    "name": "Property Constraints",
    "explain": "Outputs should fall within a specified range or set of valid values, make sure to reason about it. Functions that manipulate data structures should maintain the integrity and consistency of the structure. Make sure to reason about the constraints of the function.",
}
property_Return_Type = {
    "name": "Return Type",
    "explain": "The return type of a function should be consistent with the expected output. For example, a function that is supposed to return a list should not return a string or a number. Make sure to check the return type of the function.",
}
property_relation_to_input = {
    "name": "Relationship to Input",
    "explain": "Check if the output of the function is related to the input in a meaningful way. For example, a function that on list can return a list with the same elements or subset of elements. The size of list can be same or smaller or larger than the given. Or the return value is related to the input value. Make sure to reason about the relationship between input and output.",
}
property_trivial_return = {
    "name": "Trivial Return",
    "explain": "If the function is supposed to return a set or list like, check the minimum number of elements that should be returned. If the return is trivial, make sure to reason about it. For example, a function that is supposed to return a list should not return an empty list.",
}
property_Shuffle = {
    "name": "Shuffle",
    "explain": "If input is a list like data structure, for some functions, it is possible that shuffle of the input will not change the result.",
}
property_Easy_to_Verify = {
    "name": "Easy to Verify",
    "explain": "Some solution are difficult to find directly but can be easily verified once a solution is provided.",
}

property_list_full = [
    property_Symmetry,
    property_Alternatives,
    property_Induction,
    property_Idempotence,
    property_Invariants,
    property_Property_Constraints,
    property_Return_Type,
    property_relation_to_input,
    property_trivial_return,
    property_Shuffle,
    property_Easy_to_Verify,
]

property_list = [
    property_Symmetry,
    property_Induction,
    property_Idempotence,
    property_Property_Constraints,
    property_relation_to_input,
    property_Shuffle,
    property_trivial_return,
]

for p in property_list:
    p["explain"] += f" {suffix}"


def create_ask_info_prompt(
    function_name: str, function: str, test: str, class_structure: str
) -> tuple:
    if function:
        function = f"Function:\n```python\n{function}\n```\n\n"
    if test:
        test = f"Test:\n```python\n{test}\n```\n\n"
    if class_structure:
        class_structure = f"Class Structure:\n```python\n{class_structure}\n```\n\n"

    template = textwrap.dedent(
        """\
        What is `{}` doing?
        First write down what you think about the function, what you think about the test, what you think about the function.
        You should write down your thought process.
        The answer should follow the format:
        **Initial Thoughts**
        **Analyzing the Function**
        **Analyzing the Test**
        **More Thoughts**
        **Putting it Together**

        {}{}{}
        """
    ).format(function_name, function, class_structure, test)
    return template


def ask_create_strategy_prompt(cut, code_explanation):
    function_body = cut.function_body
    if function_body:
        function_body = f"Function:\n```python\n{function_body}\n```\n\n"
    test = cut.test
    if test:
        test = f"Test:\n```python\n{test}\n```\n\n"
    class_structure = cut.class_structure
    if class_structure:
        class_structure = f"Class Structure:\n```python\n{class_structure}\n```\n\n"
    template = textwrap.dedent(
        """\
        You are a software engineer working on a project that involves testing a function called `{}`.
        {}{}{}
        Code Explanation:
        {}

        What are the parameters for this function? Think step by step. Write your thought first. Make sure to consider whats the function expecting for each parameter. Do not code yet.
        Answer should follow the format:
        **Step 1: Analyze the function**
        **Step 2: Analyze the parameters**
            -- Restrictions of parameters
        **Step 3: Analyze the return type**
        **Step 4: Analyze the function signature**
        """
    ).format(cut.entry_point, function_body, class_structure, test, code_explanation)
    return template


def create_ask_properties_prompt(
    function_name: str, function: str, test: str, property_dict, code_explanation
) -> tuple:
    template = textwrap.dedent(
        """\
        You are a software engineer working on a project that involves testing a function called `{}`.
        You should write down your thought process, what you think about the function, what you think about the test.
        Function:
        ```python
        {}
        ```
        Test:
        ```python
        {}
        ```
        Code Explanation:
        {}

        Question:
        Answer the following question based on the function above.
        Does `{}` have the property {}? 
        {}
        This function many not have this property, write NO if this function do not have the property.
        Explane step by step.
        """
    ).format(
        function_name,
        function,
        test,
        code_explanation,
        function_name,
        property_dict["name"],
        property_dict["explain"],
    )
    return template


class pipeline_PBTFactory(Pipeline):

    def __init__(
        self,
        cut_data: CUT_data,
        max_strategy_retry=3,
        max_strategy_fix=3,
        max_retry=3,
        max_fix=3,
        max_hypothesis_examples=350,
        system_message: str = None,
    ):
        super().__init__(
            cut_data, max_retry, max_fix, max_hypothesis_examples, system_message
        )

        self.max_strategy_retry = max_strategy_retry
        self.max_strategy_fix = max_strategy_fix

    def run(self):
        code_explanation = self.ask_for_code_explanation(MessageManager())

        for i in range(self.max_strategy_retry):
            bug_free, strategy_msg, logs, err = self.create_strategy(
                MessageManager(), code_explanation
            )
            if bug_free:
                break

        if not bug_free:
            with open(f"{self.cut_data.logdir}/strategy.log", "w") as f:
                f.write(f"Strategy has error: \n{err}")
            return self.chat.total_time

        property_list = self.get_property_list(code_explanation)
        for i in range(len(property_list)):
            self.create_pbt(
                MessageManager(),
                code_explanation,
                property_list[i],
                strategy_msg,
            )

        return self.chat.total_time

    def get_property_list(self, code_explanation):
        return property_list

    def ask_for_code_explanation(self, mm: MessageManager):
        prompt = create_ask_info_prompt(
            self.cut_data.cut.entry_point,
            self.cut_data.cut.function_body,
            self.cut_data.cut.test,
            self.cut_data.cut.class_structure,
        )
        mm.add_user_message(prompt)
        msg = self.chat.ask(mm, "ask_info")
        mm.add_assistant_message(msg)
        mm.add_user_message(
            textwrap.dedent(
                """\
                Now collect your thoughts, and give me a complete summary of the function. Your summary should include the following:
                **Function Summary**
                **Input:**
                **Output:**
                **How it Works**
                **Behavior:**
                **Purpose:**
                **Example Usage**
                """
            )
        )
        msg = self.chat.ask(mm, "ask_info_summary")
        mm.add_assistant_message(msg)
        return msg

    def create_strategy(self, mm: MessageManager, code_explanation):
        msg_first = self.ask_for_strategy(mm, code_explanation)
        msg = msg_first
        bug_free = False

        exit_code, logs, logs_err = self.test_strategy(
            f"{self.cut_data.testdir}/strategy.py", find_code(msg)
        )
        if (not exit_code) and exit_code == 0:
            bug_free = True
        for i in range(self.max_strategy_fix):
            if bug_free:
                break
            msg = self.ask_fix_code(
                mm,
                logs_err,
                "Do not change anything other than strategy function.",
                "fix_code_strategy",
            )

            exit_code, logs, logs_err = self.test_strategy(
                f"{self.cut_data.testdir}/strategy.py", find_code(msg)
            )
            if (not exit_code) and exit_code == 0:
                bug_free = True

        if bug_free:
            msg = replace_code(msg_first, find_code(msg))
            return True, msg, logs, ""
        else:
            return False, msg, logs, logs_err

    def ask_for_strategy(self, mm: MessageManager, code_explanation: str):
        prompt = ask_create_strategy_prompt(self.cut_data.cut, code_explanation)
        mm.add_user_message(prompt)
        msg = self.chat.ask(mm, "create_strategy_thought")
        mm.add_assistant_message(msg)

        prompt = textwrap.dedent(
            f"""\
            Now, use python hypothesis to create strategy function. Make sure the name of function is `strategy_function`.
            Do not test on invalid input type, for example, if the function is expecting a list of integers, do not give string. \
            The return of strategy function should contain parameters for the function under test. \
            The strategy function should able to generate diverse cases. Do not call {self.cut_data.cut.entry_point} in the strategy function. \
            Recall the function signature and return type is {self.cut_data.cut.signature}.
            Think step by step. Write your thought first. Make sure to consider whats the function is doing.
            If the strategy_function going to return multiple parameters, return a dictionary. When creating complex object, use helper function.
            When coding, give me the strategy function only and only use one code block. The strategy function should start with
            ```python
            Other imports
            import hypothesis.strategies as st
            from {self.cut_data.cut.module} import {self.import_name} #  Do not change this line

            @st.composite
            def strategy_function(draw):
            ```
            """
        )
        mm.add_user_message(prompt)
        msg = self.chat.ask(mm, "create_strategy")
        mm.add_assistant_message(msg)
        if count_code(msg) != 1:
            return self.ask_for_code_only(mm)
        return msg

    def test_strategy(self, filename, code):

        with open(filename, "w") as f:
            f.write(
                "import warnings\nfrom hypothesis.errors import NonInteractiveExampleWarning\nwarnings.filterwarnings('ignore', category=NonInteractiveExampleWarning)\nwarnings.filterwarnings('ignore', category=DeprecationWarning)\n"
            )
            f.write("import hypothesis.strategies as st\n")
            for line in code.split("\n"):
                if "import" in line and self.import_name in line:
                    line = f"from {self.cut_data.cut.module} import {self.import_name}"
                f.write(line + "\n")
            f.write("\n\n\n")
            f.write("for _ in range(100):\n    strategy_function().example()\n")
        exit_code, logs, logs_err, time_taken = run_code(
            filename,
            self.cut_data.project_path,
            timeout_msg=f"Strategy timeout. {self.cut_data.cut.id}",
            log_path=self.cut_data.logdir,
        )
        return exit_code, logs, logs_err

    def create_pbt(
        self,
        mm: MessageManager,
        code_explanation,
        property_dict,
        strategy_msg,
    ) -> bool:
        prompt = create_ask_properties_prompt(
            self.cut_data.cut.entry_point,
            self.cut_data.cut.function_body,
            self.cut_data.cut.test,
            property_dict,
            code_explanation,
        )
        mm.add_user_message(prompt)
        msg = self.chat.ask(mm, f"create_pbt_{property_dict['name']}")
        mm.add_assistant_message(msg)

        if not self.ask_to_confirm_has_property(
            mm.copy(), code_explanation, property_dict
        ):
            return False, False

        prompt = "What is the strategy function for this property? Write your thought first. Make sure to consider whats the function expecting for each parameter."
        mm.add_user_message(prompt)
        mm.add_assistant_message(strategy_msg)
        for i in range(self.max_retry):
            mm2 = mm.copy()
            bug_free, test_msg, logs, err = self.ask_to_create_pbt_with_property(
                mm2, property_dict, find_code(strategy_msg)
            )
            if bug_free:
                break
        return True, bug_free

    def ask_to_confirm_has_property(
        self, mm: MessageManager, code_explanation, property_dict
    ) -> bool:
        prompt = "You are correct. Base on your explanation, do you think this property is present in the function? Write **NO** if this property is not present. Else **YES**. Do not write other than **YES** or **NO**."
        mm.add_user_message(prompt)
        msg = self.chat.ask(
            mm,
            f"create_pbt_{property_dict['name']}_check",
            request_type=RequestType.short_answer,
        )
        if "no" in msg.lower():
            return False
        return True

    def ask_to_create_pbt_with_property(
        self, mm: MessageManager, property_dict, strategy_code
    ):
        pbt_save_path = os.path.join(
            self.cut_data.testdir, f"test_{property_dict['name']}.py".replace(" ", "_")
        )

        msg = self.ask_for_pbts_code(mm, property_dict)
        max_fix = self.max_fix
        mm_backup = mm.copy()
        bug_free = False

        exit_code, logs, logs_err = self.test_pbts(
            pbt_save_path,
            self.cut_data.cut.function_body,
            strategy_code,
            find_code(msg),
        )
        if exit_code == 0:
            bug_free = True

        for i in range(max_fix):
            if bug_free:
                break
            msg = self.ask_fix_code(
                mm_backup,
                logs_err,
                textwrap.dedent(
                    """\
                    If the error is because of parameters generated by the strategy function, you should change the strategy function.
                    Remember, the test should need @given(strategy_function()) wrapper.
                    The answer should follow the format:
                    **Step 1: Analyze the error message**
                    **Step 2: Understand why the error occurs**
                    **Step 3: Modify the Code**
                    - Fixed code here
                    ERROR:
                    """
                ),
                f"fix_code_pbt_{property_dict['name']}",
            )
            exit_code, logs, logs_err = self.test_pbts(
                pbt_save_path,
                self.cut_data.cut.function_body,
                strategy_code,
                find_code(msg),
            )
            if exit_code == 0:
                bug_free = True

        if bug_free:
            return True, msg, logs, ""
        else:
            with open(pbt_save_path) as f:
                code = f.read()
            with open(
                os.path.join(
                    self.cut_data.logdir,
                    "fail",
                    f"{property_dict['name']}_{self.failed_count}.txt".replace(
                        " ", "_"
                    ),
                ),
                "w",
            ) as f:
                f.write(f"{code}\n\n{logs}\n\n{logs_err}")
            self.failed_count += 1
            os.remove(pbt_save_path)
            return False, msg, logs, logs_err

    def ask_for_pbts_code(self, mm: MessageManager, property_dict):
        # mm.replace_content(self.p.function, self.p.signature)
        prompt = textwrap.dedent(
            f"""\
            Base on analyze above, how to test for {property_dict['name']} property use property based testing? Write your thought first.
            Then, use python hypothesis to write property based testing for this property. When assert do not assume object are equable. 
            Use the strategy function above. If you need to generate specific input, modify the strategy function.
            When except Error, make sure to check the input is invalid.
            When compare float numbers, use math.isclose(a, b, rel_tol=1e-3, abs_tol=1e-3) instead of a == b.
            Assume `{self.cut_data.cut.entry_point}` is already imported in the file with `from {self.cut_data.cut.module} import {self.cut_data.cut.entry_point}`. And strategy function is already defined. Do not use placeholder.
            Make sure to call `{self.cut_data.cut.entry_point}` in the tests. Make sure test the property under test, do not test other properties.
            Recall the function signature and return type is `{self.cut_data.cut.signature}`. Remember, the test should need `@given(strategy_function())` wrapper.
            Think step by step. Write your thought first. Make sure to consider whats the function is doing and the post condition of the function.
            When coding, give me the test function only and only use one code block. Do not use placeholder. Do not use functions that are not exsiting in the code.
            Test should start with
            ```python
            other imports
            from {self.cut_data.cut.module} import {self.import_name} #  Do not change this line

            @given(strategy_function())
            def test_*(parameters):
                # Unpacking parameters if strategy_function return a dict. eg: _, _ = parameters[""], parameters[""]
            ```
            """
        )
        mm.add_user_message(prompt)
        msg = self.chat.ask(
            mm, f"create_test_{property_dict['name']}".replace(" ", "_")
        )
        mm.add_assistant_message(msg)
        if count_code(msg) != 1:
            return self.ask_for_code_only(mm)
        return msg

    def test_pbts(self, filename, src_code, strategy_code, pbt_code):
        with open(filename, "w") as f:
            f.write(
                "import warnings\nfrom hypothesis.errors import NonInteractiveExampleWarning\nwarnings.filterwarnings('ignore', category=NonInteractiveExampleWarning)\nwarnings.filterwarnings('ignore', category=DeprecationWarning)\n\n"
            )
            f.write(
                f"from hypothesis import settings\nsettings.register_profile('example', max_examples={self.max_hypothesis_examples})\nsettings.load_profile('example')\n\n"
            )
            f.write("from hypothesis import given\n")
            f.write("import math\n")
            f.write("import hypothesis.strategies as st\n")
            f.write("import pytest\n")
            f.write(f"from {self.cut_data.cut.module} import {self.import_name}\n")

            for line in strategy_code.split("\n"):
                if "import" in line and self.import_name in line:
                    line = f"from {self.cut_data.cut.module} import {self.import_name}"
                f.write(line + "\n")
            f.write("\n#END STRATEGY\n\n\n")

            for line in pbt_code.split("\n"):
                if "import" in line and self.import_name in line:
                    line = f"from {self.cut_data.cut.module} import {self.import_name}"
                elif "@settings(max_examples=" in line:
                    continue
                elif "import strategy_function" in line:
                    continue
                f.write(line + "\n")

        for i in range(4):  # try 4 times to ensure the test is not flaky
            exit_code, logs, logs_err, time_taken, timeouted = run_pytest(
                filename,
                self.cut_data.project_path,
                self.cut_data.logdir,
                timeout_msg=f"PBTs timeout. {self.cut_data.cut.id}, {filename}",
            )
            if exit_code != 0:
                return exit_code, logs, logs_err
        return exit_code, logs, logs_err
