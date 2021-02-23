#!/usr/bin/env python

import argparse
import os
from SDRF import SDRF
import re


arg_parser = argparse.ArgumentParser()

arg_parser.add_argument('-d', '--directory-with-sdrfs',
                        required=True,
                        help="Directory with SDRFs to merge"
                        )
arg_parser.add_argument('-o', '--output', required=True,
                        help="File path for output SDRF (not a directory path)."
                        )
arg_parser.add_argument('--accessions-file', required=False,
                        help="File with comma separated list of accessions to use only. "
                             "Overrides accessions list."
                        )
arg_parser.add_argument('-a', '--accessions-list', required=False,
                        help="Comma-separated list of accessions to use only."
                        )

args = arg_parser.parse_args()


def get_study_accession(filename):
    m = re.match('.*/?(?P<accession>E-.*).sdrf.txt$', filename)
    return m.group('accession')


def get_specified_accessions(args):
    accessions = None
    if args.accessions_file:
        with open(args.accessions_file, mode='r') as acc:
            accessions = acc.read().split(sep=",")
    elif args.accessions_list:
        accessions = args.accessions_list.split(sep=",")
    return accessions


final_sdrf = None
specific_accessions = get_specified_accessions(args)

for filename in os.listdir(args.directory_with_sdrfs):
    if filename.endswith(".sdrf.txt"):
        acc = get_study_accession(filename)
        if specific_accessions and acc not in specific_accessions:
            print(f"Skipping accession {acc} as it is not in the specified list..")
            continue
        print(f"Merging SDRF {filename}...")
        sdrf = SDRF(args.directory_with_sdrfs + "/" + filename)
        sdrf.add_block_comment(node="Source Name", comment_name="Study", comment_value=acc)
        sdrf.prepend_into_column(node="Assay Name",
                                 comment_name="Technical replicate group", value=acc, change_empty=False)
        if final_sdrf is None:
            final_sdrf = sdrf
        else:
            final_sdrf.merge_external(sdrf)
        of = final_sdrf.get_size_for_column(node_name="Source Name", subfield="Characteristics[strain]")
        sn = final_sdrf.get_size_for_column(node_name="Source Name", subfield=None)
        if of and of > sn:
            print(f"Issues when adding {filename}")


final_sdrf.table.to_csv(args.output, sep="\t", index=False)






