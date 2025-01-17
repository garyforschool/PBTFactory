# Enhancing Automated Test Suites Using LLMs

### ABSTRACT

Property-based testing (PBT) has the potential to detect additional failures in software, but its complexity limits its widespread use in real projects. This study focuses on generating PBT directly from source code and existing tests using large language models. We propose a multi-step pipeline for PBT generation, and evaluate it against three datasets with different levels of complexity. The paper shows that LLM-generated PBTs can identify additional bugs than the given tests. Our work demonstrates the potential to simplify property-based testing by automating PBT generation using large language models.



### Reproducing
##### Installation
Clone the repository:\
```git clone https://github.com/gwubc/EnhancingAutomatedTestSuites.git```

Install dependencies:\
```pip install -r requirements.txt```

Setup Ollama or use cloud provider:\
[https://github.com/ollama/ollama](https://github.com/ollama/ollama)\
Ensure you have the capability to run 70b models, as 7b models are insufficient for writing code.

##### Config

Create config.toml at working directory, see config_example.toml for detail and example.


##### Setup

Install requirements
`
pip install -r requirements.txt
`

Build docker to run code generated by LLM:
`
docker build -t hypothesis_docker PBTFactory/docker_scripts/
`

##### Result Structure
result_folder\
├── dataset_name\
│   ├── pipeline_name\
│   │   └── run_num\
│   │       ├── function_under_test\
│   │       │   ├── log # Not important\
│   │       │   │   ├── fail\
│   │       │   │   └── msg\
│   │       │   ├── project # Not important\
│   │       │   ├── result\
│   │       │   │   ├── cov_report\
│   │       │   │   ├── project\
│   │       │   │   ├── parsed_report.json # Important\
│   │       │   │   └── report.json\
│   │       │   └── tests # Important\
│   │       │       └── test_*.py

Note: The `result_folder` occupies 2.6 GB, with the majority of the storage consumed by the `result/cov_report` directory. This directory is primarily intended for human-readable reports and is no longer necessary once `parsed_report.json` has been created.


##### Run the program 

To run all benchmarks run

```bash
run_stdlib.sh
run_evalplus.sh
run_real_project.sh
```

Depending on the hardware, you may want to limit the maximum concurrency.


There are three datasets available: evalplus, stdlib, and real projects. 

Reproducing Evalplus Results:\
python3 -u run_evalplus.py -v -o "$folder_path" -p pipeline_PBTFactory\
-v: verbose.\
-o: output folder_path.\
-p: pipeline. One of pipeline_PBTFactory (PBTFactory), pipeline_PBTFactory_no_expert_knowledge, pipeline_pbt_baseline, pipeline_unit_test_baseline.

Reproducing Stdlib Results:\
python3 -u run_stdlib.py -v -o "$folder_path" --include_test --include_class_structure -p pipeline_PBTFactory
--include_test: include given tests.
--include_class_structure: include class structure.

Reproducing Real Project Results:\
python3 -u run_real_project.py -v -o "$folder_path" -d real_project_dataset/flutils/test_data --project_src_code real_project_dataset/flutils/flutils -p pipeline_PBTFactory\
-d: path to test data. (see Test Data Structure)\
--project_src_code: path to project source code.

To setup a project, see create_dataset/readme.md

Test Data Structure:\
test_data\
├── function_name1\
│   ├── code.py\
│   ├── setup_data.json\
│   └── test_code.py\
├── function_name2\
│   ├── code.py\
│   ├── setup_data.json\
│   └── test_code.py\
└── ...

code.py: Contains the definition of the function under test.\
setup_data.json: Contains metadata about the function. Example content:\
{"name": "parseline", "signature": "def parseline(self, line)", "startline": 91, "endline": 106, "package": "cmd_Cmd", "classname": "Cmd"}\
Note: The package value must not match any existing packages.
test_code.py: Contains the test cases.

### Reproduce tables and graph
See collect_data_table.ipynb and collect_data_plot.ipynb
