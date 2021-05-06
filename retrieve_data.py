#!/usr/bin/env python

from argparse import ArgumentParser
from requests import get
from os import path, makedirs
from sys import exit
from time import sleep


arg_parser = ArgumentParser()

arg_parser.add_argument('-i', '--input-path',
                        required=True,
                        help="Directory where <accession>/<files> will be checked and downloaded to if not present."
                        )
arg_parser.add_argument('-a', '--accessions', required=True,
                        help="List of accessions to process, comma separated"
                        )
arg_parser.add_argument('-d', '--also-data', required=False, action='store_true', dest='also_data',
                        default=False, help="Also download data (transcripts and genes raw counts) and not only metadata"
                        )
arg_parser.add_argument('-f', '--fail-on-missing', required=False, action='store_true', dest='fail_on_missing',
                        default=False, help="Exit with an error if a file cannot be downloaded"
                        )
arg_parser.add_argument('-r', '--replace', required=False, action='store_true', dest='replace',
                        default=False, help="Replace existing files."
                        )



def build_file_list(accession, also_data=False):
    """
    Returns the file list to download for a given accession

    :param accession:
    :param also_data: If true, also add data files to the list
    :return:
    >>> files = build_file_list('E-TEST-1')
    >>> 'E-TEST-1.idf.txt' in files
    True
    """
    suffix = ['-configuration.xml', '.idf.txt', '.condensed-sdrf.tsv', '.sdrf.txt']
    if also_data:
        suffix.extend(['-transcripts-raw-counts.tsv.undecorated', '-raw-counts.tsv.undecorated'])

    return [f"{accession}{x}" for x in suffix]


def download_files(accession, local_path, replace=False, fail_on_missing_file=False, also_data=False):
    """
    Downloads files from the EBI http mediated ftp server for an specific accession

    :param accession: the baseline accession for which you need files retrieved
    :param local_path:
    :param replace:
    :param fail_on_missing_file: if true, exit with an error on files that fail to download.
    :return:
    >>> import tempfile
    >>> tmp = tempfile.gettempdir()
    >>> acc = 'E-CURD-31'
    >>> download_files(accession=acc, local_path=tmp) #doctest: +ELLIPSIS
    Downloading...
    >>> path.isfile(path.join(tmp,acc,f"{acc}.idf.txt"))
    True
    """

    base_url = "http://ftp.ebi.ac.uk/pub/databases/microarray/data/atlas/experiments/"
    file_list = build_file_list(accession, also_data=also_data)
    for file in file_list:
        final_path = path.join(local_path, accession, file)
        if not path.isfile(final_path) or replace:
            makedirs(path.join(local_path, accession), exist_ok=True)
            remote_path = f"{base_url}{accession}/{file}"
            attempt = 3
            while attempt > 0:
                try:
                    print(f"Downloading {file}")
                    _download(final_path, remote_path)
                    break
                except:
                    print(f"Download failed, {attempt} attempts remaining")
                    sleep(3)
                attempt-=1
            if attempt == 0:
                if fail_on_missing_file:
                    print(f"ERROR: File {file} could not be downloaded after 3 attempts.")
                    exit(1)
                else:
                    print(f"WARNING: File {file} could not be downloaded after 3 attempts.")


def _download(final_path, remote_path):
    r = get(remote_path, allow_redirects=True)
    open(final_path, 'wb').write(r.content)


if __name__ == '__main__':
    args = arg_parser.parse_args()

    for accession in args.accessions.split(","):
        download_files(accession, local_path=args.input_path,
                       replace=args.replace,
                       fail_on_missing_file=args.fail_on_missing,
                       also_data=args.also_data
                       )


