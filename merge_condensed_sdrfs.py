#!/usr/bin/env python

import sys
import pandas as pd
import networkx as nx
import argparse
import os
from test_util import get_test_fname, get_test_path

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
                        default='organism part')
arg_parser.add_argument('--covariate-type', help='Type for main covariate, usually characteristic',
                        default='characteristic')
arg_parser.add_argument('--covariate-skip-values',
                        help="Covariate values to skip when assessing the studies connectivity; "
                             "a commma separated list of values",
                        default="", required=False
                        )

def merged_condensed(accessions, input_path, batch_type, batch_characteristic, new_accession):
    """
    Merges a set of condensed SDRFs (defined in accessions) available at <input_path>/accession/accession.condensed-sdrf.tsv,
    adding lines for the new accession under field <batch-type>/<batch> (usually characteristic / study)

    :param accessions: list of accessions to merge, they must be available within input_path
    :param input_path: path where to find <accession>/<accession>.condensed-sdrf.tsv entries
    :param batch_type: type of SDRF field where to put the batch, "characteristic" by default.
    :param batch_characteristic: name for the batch field, "study" by default.
    :param new_accession: New accession to add to the merged condensed.
    :return: a pandas merged condensed table.

    >>> accessions = ['E-GEOD-55866','E-GEOD-55482', 'E-CURD-31', 'E-GEOD-53197']
    >>> input_path = get_test_fname("condensed-merge")
    >>> cond_df = merged_condensed(accessions, input_path, batch_type='characteristic', batch_characteristic='study', new_accession="E-CURD-X")
    Parsing E-GEOD-55866 condensed SDRF..
    Parsing E-GEOD-55482 condensed SDRF..
    Parsing E-CURD-31 condensed SDRF..
    Parsing E-GEOD-53197 condensed SDRF..
    >>> cond_df.shape[0]
    873
    """
    cond_cols = ['Accession', 'Array', 'Sample', 'Annot_type', 'Annot', 'Annot_value', 'Annot_ont_URI']
    cond = pd.DataFrame()
    for acc in accessions:
        print(f"Parsing {acc} condensed SDRF..")
        cond_a = pd.read_csv(f"{input_path}/{acc}/{acc}.condensed-sdrf.tsv", sep="\t", names=cond_cols)
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
    >>> accessions = ['E-GEOD-55866','E-GEOD-55482', 'E-CURD-31', 'E-GEOD-53197']
    >>> input_path = get_test_fname("condensed-merge")
    >>> cond_df = merged_condensed(accessions, input_path, batch_type='characteristic', batch_characteristic='study', new_accession="E-CURD-X") #doctest: +ELLIPSIS
    Parsing ...
    >>> conn_components = cluster_samples(cond=cond_df, main_covariate="organism part", covariate_type="characteristic", batch_characteristic="study", batch_type="characteristic", covariate_skip_values=[]) #doctest: +ELLIPSIS
    Complete list of covariates: 4 ['silique', 'aerial part', 'root', 'floral bud']
    ...
    >>> len(conn_components[0].nodes)
    3
    """
    # Use unified condensed based table to produce the plot to choose batches.
    G = nx.Graph()
    covariate_values = cond.loc[(cond.Annot == main_covariate) & (cond.Annot_type == covariate_type)] \
        .Annot_value.unique().tolist()
    if not covariate_values:
        raise ValueError("No covariate values found, probably a wrong choice in main covariate or covariate type.")
    print(f"Complete list of covariates: {str(len(covariate_values))} {covariate_values}")
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
    if conn_components:
        print(f"Number of connected components: {str(len(conn_components))}")
        largest_conn_comp = max(conn_components, key=len)
        print(f"Largest connected component size: {str(len(largest_conn_comp))}")
        conn_components.sort(key=len, reverse=True)
        first_cc_covariates = []
        second_cc_covariates = []
        for cc in conn_components:
            print(f"CC number of batches: {str(len(cc))}")
            print(f"CC batches: {cc.nodes}")
            covariates_cc = set()
            for edge_cov in cc.edges.data('covariate'):
                covariates_cc.update(edge_cov[2])
            if not second_cc_covariates and first_cc_covariates:
                second_cc_covariates.extend(covariates_cc)
            if not first_cc_covariates:
                first_cc_covariates.extend(covariates_cc)
            print(f"CC number of covariates: {str(len(covariates_cc))}")
            print(f"CC covariates: {covariates_cc}\n")

        if second_cc_covariates:
            print("To extend a connected component, find new experiments that have covariates from that"
            " component and another component.")
            print("For instance, to extend the first component with all the elements of the second component,")
            print(f"find a new study for the organism that has at least one element from {first_cc_covariates} as covariate")
            print(f"and at least one element from {second_cc_covariates} as covariate.\n")
    else:
        print("Probably something wrong as no connected components are available...")

    return conn_components


if __name__ == '__main__':
    args = arg_parser.parse_args()

    # Initial merge of all datasets.
    # TODO it is a bit inconvenient currently that:
    # 1.- you need to provide the directory and the list
    cond = merged_condensed(accessions=args.accessions.split(","),
                            input_path=args.input_path,
                            batch_type=args.batch_type,
                            batch_characteristic=args.batch,
                            new_accession=args.new_accession
                            )

    try:
        conn_components = cluster_samples(cond=cond,
                                          main_covariate=args.covariate,
                                          covariate_type=args.covariate_type,
                                          covariate_skip_values=args.covariate_skip_values,
                                          batch_characteristic=args.batch,
                                          batch_type=args.batch_type
                                          )
    except ValueError as e:
        sys.exit(e)

    chosen_batches = list(conn_components[0].nodes)

    blessed_condensed = merged_condensed(accessions=chosen_batches,
                                         input_path=args.input_path,
                                         batch_type=args.batch_type,
                                         batch_characteristic=args.batch,
                                         new_accession=args.new_accession
                                         )

    # make sure output directory exists.
    from pathlib import Path
    Path(args.output).mkdir(parents=True, exist_ok=True)

    blessed_condensed.to_csv(path_or_buf=os.path.join(args.output, f"{args.new_accession}.condensed.sdrf.tsv"), sep="\t",
                             index=False, header=False)

    with open(os.path.join(args.output, f"{args.new_accession}.selected_studies.txt"), "w") as ss:
        ss.write(",".join(chosen_batches))
