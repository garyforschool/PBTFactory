import argparse
import concurrent.futures
import logging
import os

import PBTFactory
from PBTFactory.chat import RequestManager
from PBTFactory.cut_data import CUT_data
from PBTFactory.get_args import get_args
from PBTFactory.get_code_real_project import get_code_real_project, setup_for_real_project

if __name__ == "__main__":
    args = get_args()

    if args.project_src_code == "":
        raise ValueError("Please provide the path to the project source")
    if args.dataset == "":
        raise ValueError("Please provide the path to the dataset")

    cut_datas = []
    for i in sorted(os.listdir(args.dataset))[:]:
        cut = get_code_real_project(os.path.join(args.dataset, i))
        _, testdir, resultdir, logdir = setup_for_real_project(cut, args.out)
        cut_datas.append(
            CUT_data(cut, args.project_src_code, testdir, resultdir, logdir)
        )

    PBTFactory.main(args, cut_datas)
