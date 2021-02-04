#!/usr/bin/env python

import pandas as pd
import networkx as nx
import argparse
import os

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument('-d', '--input-path',
                        required=True,
                        help="Directory with condensed SDRFs to merge"
                        )
arg_parser.add_argument('-a', '--accessions', required=True,
                        help="List of accessions to process, comma separated"
                        )
arg_parser.add_argument('-o', '--output', required=True,
                        help="Path for output. <new-accession>.condensed.sdrf.tsv "
                             "and <new-accession>.selected_studies.txt will be created there."
                        )
arg_parser.add_argument('-n', '--new-accession', help='New accession for the output', required=True)
arg_parser.add_argument('-b', '--batch', help='Header for storing batch or study', default='study')
arg_parser.add_argument('-t', '--batch-type', help='Type for batch, usually characteristic', default='characteristic')
arg_parser.add_argument('-c', '--covariate', help='Header for main covariate, usually organism part',
                        default='organism_part')
arg_parser.add_argument('--covariate-type', help='Type for main covariate, usually characteristic',
                        default='characteristic')
arg_parser.add_argument('--covariate-skip-values',
                        help="Covariate values to skip when assessing the studies connectivity; "
                             "a commma separated list of values",
                        default="", required=False
                        )

args = arg_parser.parse_args()


def merged_condensed(accessions, input_path, batch_type, batch_characteristic, new_accession):
    cond = pd.DataFrame()
    for acc in accessions:
        print("Parsing {} condensed SDRF..".format(acc))
        cond_a = pd.read_csv("{}/{}/{}.condensed-sdrf.tsv".format(input_path, acc, acc), sep="\t", names=cond_cols)
        cond_a['Accession'] = new_accession
        input = {}
        samples = cond_a.Sample.unique().tolist()
        input['Annot_type'] = [batch_type] * len(samples)
        input['Annot'] = [batch_characteristic] * len(samples)
        input['Accession'] = [new_accession] * len(samples)
        input['Annot_value'] = [acc] * len(samples)
        input['Sample'] = []
        for sample in samples:
            input['Sample'].append(sample)

        cond_a = cond_a.append(pd.DataFrame.from_dict(input))
        cond = cond.append(cond_a)

    return cond


def cluster_samples(cond: pd, main_covariate: str, covariate_type: str,
                    covariate_skip_values: list, batch_characteristic: str,
                    batch_type: str):
    """
    Takes the unified condensed SDRF Pandas Dataframe and builds a graph where each study
    is a node and the specified covariate (usually an organism part) generates the edges. Two studies are connected if
    they share a covariate value among their samples (one study => many covariate values for the specified field).

    From this graph, the connected components are extracted and given in order in the returned
    result.

    :param cond:
    :param main_covariate:
    :param covariate_type:
    :param covariate_skip_values:
    :param batch_characteristic:
    :param batch_type:
    :return:
    """
    # Use unified condensed based table to produce the plot to choose batches.
    G = nx.Graph()
    covariate_values = cond.loc[(cond.Annot == main_covariate) & (cond.Annot_type == covariate_type)] \
        .Annot_value.unique().tolist()
    print("Complete list of covariates: {} {}".format(str(len(covariate_values)), covariate_values))
    for cov in covariate_values:
        print("Processing cov: {}".format(cov))
        if cov in covariate_skip_values:
            continue
        # cov to samples
        samples = cond.loc[(cond.Annot == main_covariate) \
                           & (cond.Annot_type == covariate_type) \
                           & (cond.Annot_value == cov)].Sample.unique().tolist()
        # samples to batch
        batches = cond.loc[cond.Sample.isin(samples) \
                           & (cond.Annot == batch_characteristic) \
                           & (cond.Annot_type == batch_type)].Annot_value.unique().tolist()

        for i in range(len(batches)):
            for j in range(i + 1):
                if G.has_edge(batches[i], batches[j]):
                    G.edges[batches[i], batches[j]]['covariate'].update([cov])
                else:
                    G.add_edge(batches[i], batches[j], covariate=set([cov]))
    conn_components = [G.subgraph(c).copy() for c in nx.connected_components(G)]
    print("Number of connected components: {}".format(str(len(conn_components))))
    largest_conn_comp = max(conn_components, key=len)
    print("Largest connected component size: {}".format(str(len(largest_conn_comp))))
    conn_components.sort(key=len, reverse=True)
    for cc in conn_components:
        print("CC number of batches: {}".format(str(len(cc))))
        print("CC batches: {}".format(cc.nodes))
        covariates_cc = set()
        for edge_cov in cc.edges.data('covariate'):
            covariates_cc.update(edge_cov[2])
        print("CC number of covariates: {}".format(str(len(covariates_cc))))
        print("CC covariates: {}".format(covariates_cc))
        print()

    return conn_components


# Initial merge of all datasets.
# TODO it is a bit inconvenient currently that:
# 1.- you need to provide the directory and the list
cond = merged_condensed(accessions=args.accessions.split(","),
                        input_path=args.input_path,
                        batch_type=args.batch_type,
                        batch_characteristic=args.batch,
                        new_accession=args.new_accession
                        )

conn_components = cluster_samples(cond=cond,
                                  main_covariate=args.covariate,
                                  covariate_type=args.covariate_type,
                                  covariate_skip_values=args.covariate_skip_values)

chosen_batches = list(conn_components[0].nodes)

blessed_condensed = merged_condensed(accessions=chosen_batches,
                                     input_path=args.input_path,
                                     batch_type=args.batch_type,
                                     batch_characteristic=args.batch,
                                     new_accession=args.new_accession
                                     )

blessed_condensed.to_csv(path_or_buf=os.path.join(args.output, f"{args.new_accesion}.condensed.sdrf.tsv"), sep="\t", index=False)

with open(file=os.path.join(args.output, f"{args.new_accession}.selected_studies.txt")) as ss:
    ss.write(",".join(chosen_batches))
