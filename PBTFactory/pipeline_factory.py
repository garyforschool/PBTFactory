from PBTFactory.cut_data import CUT_data
from PBTFactory.pipeline import IPipeline

from PBTFactory.pipeline_PBTFactory import pipeline_PBTFactory
from PBTFactory.pipeline_PBTFactory_no_expert_knowledge import pipeline_PBTFactory_no_expert_knowledge
from PBTFactory.pipeline_pbt_baseline import pipeline_pbt_baseline
from PBTFactory.pipeline_unit_test_baseline import pipeline_unit_test_baseline


class PipelineFactory:
    def __init__(self, pipeline_type: str, config: dict):
        required_keys = ["max_retry", "max_fix", "max_hypothesis_examples"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")
        if "system_message" in config:
            self.system_message = config["system_message"]
        else:
            self.system_message = None

        self.pipeline_type = pipeline_type
        self.config = config

    def create(self, cut_data: CUT_data) -> IPipeline:
        if self.pipeline_type == "pipeline_unit_test_baseline":
            return pipeline_unit_test_baseline(
                cut_data,
                max_retry=self.config["max_retry"],
                max_fix=self.config["max_fix"],
                max_hypothesis_examples=self.config["max_hypothesis_examples"],
                system_message=self.system_message,
            )

        if self.pipeline_type == "pipeline_pbt_baseline":
            return pipeline_pbt_baseline(
                cut_data,
                max_retry=self.config["max_retry"],
                max_fix=self.config["max_fix"],
                max_hypothesis_examples=self.config["max_hypothesis_examples"],
                system_message=self.system_message,
            )

        if self.pipeline_type == "pipeline_PBTFactory":
            assert "max_strategy_retry" in self.config
            assert "max_strategy_fix" in self.config
            return pipeline_PBTFactory(
                cut_data,
                max_retry=self.config["max_retry"],
                max_fix=self.config["max_fix"],
                max_strategy_retry=self.config["max_strategy_retry"],
                max_strategy_fix=self.config["max_strategy_fix"],
                max_hypothesis_examples=self.config["max_hypothesis_examples"],
                system_message=self.system_message,
            )

        if self.pipeline_type == "pipeline_PBTFactory_no_expert_knowledge":
            assert "max_strategy_retry" in self.config
            assert "max_strategy_fix" in self.config
            return pipeline_PBTFactory_no_expert_knowledge(
                cut_data,
                max_retry=self.config["max_retry"],
                max_fix=self.config["max_fix"],
                max_strategy_retry=self.config["max_strategy_retry"],
                max_strategy_fix=self.config["max_strategy_fix"],
                max_hypothesis_examples=self.config["max_hypothesis_examples"],
                system_message=self.system_message,
            )

        raise ValueError(f"Invalid pipeline type: {self.pipeline_type}")
