import argparse
import concurrent.futures
import logging

import PBTFactory
from PBTFactory.chat import RequestManager
from PBTFactory.cut_data import CUT_data
from PBTFactory.get_args import get_args
from PBTFactory.get_code_evalplus import get_code_evalplus, setup_for_evalplus

if __name__ == "__main__":
    args = get_args()

    cut_datas = []
    for i in range(164):  # len(get_human_eval_plus().items()) = 164
        cut = get_code_evalplus(f"HumanEval/{i}")
        project_path, testdir, resultdir, logdir = setup_for_evalplus(cut, args.out)
        cut_datas.append(CUT_data(cut, project_path, testdir, resultdir, logdir))

    PBTFactory.main(args, cut_datas)

