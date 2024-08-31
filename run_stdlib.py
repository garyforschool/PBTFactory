import argparse
import os

import PBTFactory
from PBTFactory.cut_data import CUT_data
from PBTFactory.get_args import get_args
from PBTFactory.get_code_stdlib import get_code_stdlib, setup_for_stdlib

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--include_test", help="include unit test", action="store_true")
    parser.add_argument(
        "--include_class_structure", help="include class structure", action="store_true"
    )
    args = get_args(parser)

    cut_datas = []
    for folder in sorted(os.listdir(args.dataset)):
        cut = get_code_stdlib(os.path.join(args.dataset, folder))
        if not args.include_test:
            cut.test = ""
        if not args.include_class_structure:
            cut.class_structure = ""

        project_path, testdir, resultdir, logdir = setup_for_stdlib(cut, args.out)
        cut_datas.append(CUT_data(cut, project_path, testdir, resultdir, logdir))

    PBTFactory.main(args, cut_datas)

