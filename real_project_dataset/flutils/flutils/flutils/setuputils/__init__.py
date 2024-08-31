from os import PathLike
from typing import Any, Dict, Optional, Union
from .cfg import each_sub_command_config
from .cmd import build_setup_cfg_command_class


def add_setup_cfg_commands(
    setup_kwargs: Dict[str, Any], setup_dir: Optional[Union[PathLike, str]] = None
) -> None:
    for sub_command_cfg in each_sub_command_config(setup_dir):
        klass = build_setup_cfg_command_class(sub_command_cfg)
        if "cmdclass" not in setup_kwargs.keys():
            setup_kwargs["cmdclass"] = {}
        setup_kwargs["cmdclass"][sub_command_cfg.name] = klass
