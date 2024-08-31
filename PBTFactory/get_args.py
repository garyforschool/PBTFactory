import argparse
import os

from PBTFactory.request_manager import RequestType


# Copy from https://stackoverflow.com/questions/14117415/how-can-i-constrain-a-value-parsed-with-argparse-for-example-restrict-an-integ
def check_positive_int(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue


def load_config_from_toml_file(toml_file):
    import toml

    if not os.path.exists(toml_file):
        raise ValueError(f"Config file {toml_file} not found")
    with open(toml_file) as f:
        config = toml.load(f)
    return config


def get_args(parser: argparse.ArgumentParser = None):
    if parser is None:
        parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument("-o", "--out", help="Output dir")
    parser.add_argument(
        "-p", "--pipeline", help="Pipeline to use.", default="pipeline_pbt_v1"
    )
    parser.add_argument("-v", "--verbose", help="Verbose", action="store_true")
    parser.add_argument("-d", "--dataset", help="Path to dataset.", default="dataset")
    parser.add_argument("--project_src_code", help="Path project code.", default="")
    parser.add_argument(
        "--config_file",
        help="Config file.",
        default="config.toml",
    )

    args = parser.parse_args()
    config_from_file = load_config_from_toml_file(args.config_file)
    args.llm_server_configs = {}
    for k, v in config_from_file["llm_servers"].items():
        if "base_url" not in v or "model" not in v:
            raise ValueError(f"Invalid llm_server config: {k}: {v}")

        if "enabled" not in v:
            v["enabled"] = True
        if not v["enabled"]:
            continue

        if "concurrent" not in v:
            v["concurrent"] = 1

        if "retry" not in v:
            v["retry"] = 4

        if "allow_request_type" not in v or v["allow_request_type"] == []:
            v["allow_request_type"] = RequestType.get_all_types()
        v["allow_request_type"] = [
            RequestType.from_string(x) for x in v["allow_request_type"]
        ]
        args.llm_server_configs[k] = v

    if "max_workers" not in config_from_file:
        config_from_file["max_workers"] = 3
    if "max_retry" not in config_from_file:
        config_from_file["max_retry"] = 3
    if "max_fix" not in config_from_file:
        config_from_file["max_fix"] = 1
    if "max_strategy_retry" not in config_from_file:
        config_from_file["max_strategy_retry"] = 3
    if "max_strategy_fix" not in config_from_file:
        config_from_file["max_strategy_fix"] = 1
    if "max_hypothesis_examples" not in config_from_file:
        config_from_file["max_hypothesis_examples"] = 500
    if "verbose" not in config_from_file:
        config_from_file["verbose"] = False

    args.max_workers = check_positive_int(config_from_file["max_workers"])
    args.max_retry = check_positive_int(config_from_file["max_retry"])
    args.max_fix = check_positive_int(config_from_file["max_fix"])
    args.max_strategy_retry = check_positive_int(config_from_file["max_strategy_retry"])
    args.max_strategy_fix = check_positive_int(config_from_file["max_strategy_fix"])
    args.max_hypothesis_examples = check_positive_int(
        config_from_file["max_hypothesis_examples"]
    )
    if "system_message" in config_from_file:
        args.system_message = config_from_file["system_message"]
    else:
        args.system_message = None
    return args
