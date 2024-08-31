To create a dataset from large Python projects:

Step 1:
Create a folder named dataset/project_name.

Step 2:
Modify main.py to update the project_root and out_path.

Step 3:
Run the command:
`python main.py`

This step will create calls.csv, which is for debugging and can be safely deleted.

The folder specified in out_path will be created and will contain functions under test with their corresponding unit tests.


Acknowledgment: The find_usages tool was created by Jifeng Wu [https://abbaswu.github.io/].