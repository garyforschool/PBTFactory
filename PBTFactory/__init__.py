import concurrent.futures
import json
import logging
import os
import threading
import time

from PBTFactory.chat import RequestManager
from PBTFactory.cut_data import CUT_data
from PBTFactory.pipeline import IPipeline
from PBTFactory.pipeline_factory import PipelineFactory
from PBTFactory.summary import summary

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)


def run(cut_data: CUT_data, pipeline_factory: PipelineFactory):
    timeused = 0
    try:
        pipeline: IPipeline = pipeline_factory.create(cut_data)
        if not pipeline.have_finished():
            timeused = pipeline.run()
            result = pipeline.eval_test()
        else:
            with open(
                os.path.join(cut_data.resultdir, "parsed_report.json"),
            ) as f:
                result = json.load(f)
    except Exception as e:
        logging.error(f"Error creating or running pipeline:\n{e}", exc_info=True)
        raise e
    # result["timeused"] = timeused
    return result


def main(args, list_of_cut_data: list[CUT_data]):
    if len(args.llm_server_configs) == 0:
        raise ValueError("No llm_servers found in config file")

    logging.info(
        f"Pipeline: {args.pipeline}. Model: {', '.join([llm_server['model'] for llm_server in args.llm_server_configs.values()])}"
    )

    RequestManager.init(config={"llm_servers": args.llm_server_configs.values()})
    RequestManager().verbose = args.verbose

    factory = PipelineFactory(
        args.pipeline,
        {
            "max_retry": args.max_retry,
            "max_fix": args.max_fix,
            "max_strategy_retry": args.max_strategy_retry,
            "max_strategy_fix": args.max_strategy_fix,
            "max_hypothesis_examples": args.max_hypothesis_examples,
            "system_message": args.system_message,
        },
    )

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=args.max_workers
    ) as executor:
        results = []
        futures = [
            executor.submit(run, cut_data, factory) for cut_data in list_of_cut_data
        ]

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if args.verbose:
                    print(result)
                results.append(result)
            except Exception as e:
                logging.error(f"Error:\n{e}")

        RequestManager().stop = True

    summary_result = summary(results)
    print(summary_result)
    for result in results:
        print(result)
