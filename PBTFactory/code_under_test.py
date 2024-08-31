class code_under_test:
    def __init__(
        self,
        id: str,
        signature: str,
        entry_point: str,
        function_body: str,
        test: str,
        class_structure: str = "",
    ):
        self.id = id
        self.signature = signature
        self.entry_point = entry_point
        self.function_body = function_body
        self.test = test
        self.class_structure = class_structure

        self.module = None
        self.project_path = None
        self.filepath = None

        self.testdir = None
        self.resultdir = None
        self.logdir = None

        self.start_line = 0
        self.end_line = 10000

    def __str__(self):
        return self.id

    def __repr__(self):
        return (
            f"Problem ID: {self.id}\n"
            f"Function Body: {self.function_body}\n"
            f"Test: {self.test}\n"
            f"Signature: {self.signature}\n"
            f"Entry Point: {self.entry_point}"
        )
