#!/usr/bin/env python

import pandas as pd
import argparse
from test_util import get_test_fname, get_test_path


def get_sample_accession_table(condensed_path):
    """
    Returns a sample to accession table with unique rows
    :param condensed_path:
    :return:
    >>> table = get_sample_accession_table(get_test_fname("E-TEST-1.condensed-sdrf.tsv"))
    >>> table.shape[0]
    11
    >>> table.loc[table["Sample"] == "SRR1019221"].Accession.values[0]
    'E-GEOD-51763'
    """
    cond_cols = ['Accession', 'Array', 'Sample', 'Annot_type', 'Annot', 'Annot_value', 'Annot_ont_URI']
    condensed = pd.read_csv(condensed_path, sep="\t", names=cond_cols)
    sample_accession_table = condensed.loc[
        (condensed["Annot_type"] == "characteristic") & (condensed["Annot"] == "study"),
        ["Sample","Annot_value"]].drop_duplicates()
    sample_accession_table.rename(columns={'Annot_value': 'Accession'}, inplace=True)
    return sample_accession_table


def merge_data(sample_accession_table, join_type, index_col, input_path, file_suffix):
    """
    Joins through 'join_type' the different tables of data through the common 'index_col',
    selecting only the samples available for each accession in the 'sample_accession_table'.
    Data is merged from files (tab separated) available in <input_path>/<accession><file_suffix>.
    The columns of these files need to container the 'index_col' and the samples as written in
    the sample_accession_table.

    :param sample_accession_table: pandas dataframe with a column for Sample and a column for Accession.
    :param join_type: Any supported by Pandas merge function (how field)
    :param index_col: The name of the column used to join at each iteration. It is the same for all files.
    :param input_path: base directory for data files
    :param file_suffix: portion of the file after <accession>
    :return: merged pandas dataframe.
    >>> table = get_sample_accession_table(get_test_fname("E-TEST-1.condensed-sdrf.tsv"))
    >>> result = merge_data(sample_accession_table=table, join_type="inner", index_col="Gene ID", input_path=get_test_path(), file_suffix="-fake-counts.tsv")
    >>> result.shape[0]
    8
    >>> result.shape[1]
    12
    >>> result = merge_data(sample_accession_table=table, join_type="outer", index_col="Gene ID", input_path=get_test_path(), file_suffix="-fake-counts.tsv")
    >>> result.shape[0]
    9
    """
    merged = None
    for accession in sample_accession_table.Accession.unique().tolist():
        data = pd.read_csv(f"{input_path}/{accession}{file_suffix}", sep="\t")
        cols = [index_col]
        cols.extend(sample_accession_table.loc[sample_accession_table['Accession'] == accession].Sample.unique().tolist())
        # select the samples
        data = data[cols]
        if merged is None:
            merged = data
        else:
            # join on the column
            merged = pd.merge(merged, data, how=join_type, on=index_col)

    return merged


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description="Merges data where samples are in columns, based on samples listed in the condensed SDRF given.",
        epilog="Assumes that the accessions are under characteristic - study to make the sample to accession link. "
               "Data files need to be available at <input-path>/<accession><suffix>")

    arg_parser.add_argument('-d', '--input-path',
                            required=True,
                            help="Directory with data to merge"
                            )
    arg_parser.add_argument('-o', '--output', required=True,
                            help="Path for output file."
                            )
    arg_parser.add_argument('-s', '--suffix', required=False,
                            help="Suffix for counts file after <path>/<accession><suffix>",
                            default="-raw-counts.tsv.undecorated")
    arg_parser.add_argument('-c', '--merged-condensed', required=True,
                            help="Path to a merged condensed SDRF, where the sample is equivalent to what is listed in the data file columns")
    arg_parser.add_argument('-i', '--index-column', help='Column to join on', required=True)
    arg_parser.add_argument('-r', '--remove-rows-with-empty', type=bool,
                            help="If set, removes rows that have empty values")

    args = arg_parser.parse_args()

    # load the condensed SDRF and make an accession to samples structure
    sample_accession = get_sample_accession_table(args.merged_condensed)

    merge_type = "outer"
    if args.remove_rows_with_empty:
        merge_type = "inner"  # inner join: only what is shared by the two pds being merged

    result = merge_data(sample_accession_table=sample_accession,
                        join_type=merge_type,
                        index_col=args.index_column,
                        input_path=args.input_path,
                        file_suffix=args.suffix)

    result.to_csv(args.output, sep="\t", index=False)









