![PyPI](https://img.shields.io/pypi/v/MAGE-Tab-merger)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/ebi-gene-expression-group/MAGE-Tab-merger/Python%20CI)

# MAGE-Tab Merger

This package facilitates merging of MAGE-Tab components at different levels.

Source code available at: https://github.com/ebi-gene-expression-group/MAGE-Tab-merger

Note: IDF merging is still work in progress.

## Installation

We recommend that you create a [Python 3 virtual environment](https://docs.python.org/3/library/venv.html#creating-virtual-environments),
activate it (keep reading on the previous link), and then install there:

```
pip install --upgrade pip
pip install MAGE-Tab-merger
```

Once installed, you need to activate that virtual environment before using it every time that you open a new shell.

## Obtain data from Expression Atlas FTP

If all the data that you want to merge is publicly available within Expression Atlas, then you can use this convenience
call to get all the needed data for a set of Atlas studies:

```
usage: retrieve_data.py [-h] -i INPUT_PATH -a ACCESSIONS [-d] [-f] [-r]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_PATH, --input-path INPUT_PATH
                        Directory where <accession>/<files> will be checked and downloaded to if not present.
  -a ACCESSIONS, --accessions ACCESSIONS
                        List of accessions to process, comma separated
  -d, --also-data       Also download data (transcripts and genes raw counts) and not only metadata
  -f, --fail-on-missing
                        Exit with an error if a file cannot be downloaded
  -r, --replace         Replace existing files.
```


## SDRF with no considerations on metadata

This functionality will simply produce a new SDRF out of all the SDRFs provided, taking care to follow all the structure
in MAGE graph encoded inside the SDRFs.

```bash
usage: merge_sdrfs.py [-h] -d DIRECTORY_WITH_SDRFS -o OUTPUT [--accessions-file ACCESSIONS_FILE] [-a ACCESSIONS_LIST]

optional arguments:
  -h, --help            show this help message and exit
  -d DIRECTORY_WITH_SDRFS, --directory-with-sdrfs DIRECTORY_WITH_SDRFS
                        Directory with SDRFs to merge
  -o OUTPUT, --output OUTPUT
                        File path for output SDRF (not a directory path)..
  --accessions-file ACCESSIONS_FILE
                        File with comma separated list of accessions to use only. Overrides accessions list.
  -a ACCESSIONS_LIST, --accessions-list ACCESSIONS_LIST
                        Comma-separated list of accessions to use only.
```

## Merge condensed SDRFs based on meta-data relations

Towards running meta-analysis of multiple experiments, often meta-analysis algorithms will require
that there is certain links between studies in terms of a metadata field. For instance, if the main
covariate is expected to be the organism part when merging studies (so that you can answer questions like
what is the expression of gene X in organism part Y based on all studies), then each study being merged
needs to have samples in an organism part that one of the other studies at least has.

This functionality takes condensed SDRFs for multiple studies (which can be generated with the condensed_sdrf.pl script, part of
atlas-perl-modules conda package) and suggest (and merge) the largest group of studies that can be merged to satisfy
the metadata condition explained.

```bash
usage: merge_condensed_sdrfs.py [-h] -d INPUT_PATH -a ACCESSIONS -o OUTPUT -n NEW_ACCESSION [-b BATCH] [-t BATCH_TYPE] [-c COVARIATE] [--covariate-type COVARIATE_TYPE] [--covariate-skip-values COVARIATE_SKIP_VALUES]

optional arguments:
  -h, --help            show this help message and exit
  -d INPUT_PATH, --input-path INPUT_PATH
                        Directory with condensed SDRFs to merge
  -a ACCESSIONS, --accessions ACCESSIONS
                        List of accessions to process, comma separated
  -o OUTPUT, --output OUTPUT
                        Path for output. <new-accession>.condensed.sdrf.tsv and <new-accession>.selected_studies.txt will be created there.
  -n NEW_ACCESSION, --new-accession NEW_ACCESSION
                        New accession for the output
  -b BATCH, --batch BATCH
                        Header for storing batch or study
  -t BATCH_TYPE, --batch-type BATCH_TYPE
                        Type for batch, usually characteristic
  -c COVARIATE, --covariate COVARIATE
                        Header for main covariate, usually organism part
  --covariate-type COVARIATE_TYPE
                        Type for main covariate, usually characteristic
  --covariate-skip-values COVARIATE_SKIP_VALUES
                        Covariate values to skip when assessing the studies connectivity; a commma separated list of values
```

This will compute a graph with studies as nodes. Two studies will be connected if they share a covariate field value for any set of samples.
So, for instance, if study A has organism parts lung, liver and pancreas, study B has organism parts liver and kidney,
then study A and B will be connected by one edge because of both having liver. Out of this graph,
the largest connected component will be selected and merged into a single condensed SDRF.

Two files will be created in the output directory:

- <new-accession>.condensed.sdrf.tsv
- <new-accession>.selected_studies.txt

The stdout will contain useful information about the main connected components.

Because some experiments may contain covariate values that are not useful, such as "whole organism" for organism part,
then the `--covariate-skip-values` allows to skip such values from the graph creation.

If you need an SDRF with the equivalent merged content, then use the first script listed here limited to the accessions
that where selected by this process.

## Merge assay groups XMLs for baseline experiments

In Expression Atlas MAGE-Tab files are often accompanied by XML files that encode
relations between assay groups. For baseline studies, these are generated from the SDRF. For loading merged studies,
a merged XML config file is needed (as with any baseline experiment).

Given a set of configuration XML files, named as <ACCESSION>-configuration.xml and a set of accessions,
the following can be run to merge them into a single XML:

```
usage: merge_baseline_configuration_xmls.py [-h] -x DIRECTORY_WITH_CONFIGURATION_FILES
                                            [--accessions-file ACCESSIONS_FILE] [-a ACCESSIONS_LIST] -o
                                            OUTPUT -n NEW_ACCESSION

optional arguments:
  -h, --help            show this help message and exit
  -x DIRECTORY_WITH_CONFIGURATION_FILES, --directory-with-configuration-files DIRECTORY_WITH_CONFIGURATION_FILES
                        Directory with configuration XMLs to merge
  --accessions-file ACCESSIONS_FILE
                        File with comma separated list of accessions to use only. Overrides accessions
                        list.
  -a ACCESSIONS_LIST, --accessions-list ACCESSIONS_LIST
                        Comma-separated list of accessions to use only.
  -o OUTPUT, --output OUTPUT
                        Path for output. <new-accession>-configuration.xml will be created there.
  -n NEW_ACCESSION, --new-accession NEW_ACCESSION
                        New accession for the output
```


## Convenience method for data merging

Often it is the case that data needs to be merged into some format for later data analysis steps. The
convenience method `merge_data.py` is aimed at that. Given a merged condensed SDRF where the `characteristic:study`
encodes the accession of each original experiment, and data files available at `data/` path (for the sake of the example)
named `<accession>-counts.tsv` where each sample is a column and there is a "Gene ID" index column on each of those files
then executing:

```
merge_data.py -d data -s "-counts.tsv" -o merged_result.tsv -c condensed_SDRF.tsv -i "Gene ID" --remove-rows-with-empty
```

produces a merged data set with all desired samples. More info:

```
usage: merge_data.py [-h] -d INPUT_PATH -o OUTPUT [-s SUFFIX] -c MERGED_CONDENSED -i INDEX_COLUMN [-r REMOVE_ROWS_WITH_EMPTY]

Merges data where samples are in columns, based on samples listed in the condensed SDRF given.

optional arguments:
  -h, --help            show this help message and exit
  -d INPUT_PATH, --input-path INPUT_PATH
                        Directory with data to merge
  -o OUTPUT, --output OUTPUT
                        Path for output file.
  -s SUFFIX, --suffix SUFFIX
                        Suffix for counts file after <path>/<accession><suffix>
  -c MERGED_CONDENSED, --merged-condensed MERGED_CONDENSED
                        Path to a merged condensed SDRF, where the sample is equivalent to what is listed in the data file columns
  -i INDEX_COLUMN, --index-column INDEX_COLUMN
                        Column to join on
  -r REMOVE_ROWS_WITH_EMPTY, --remove-rows-with-empty REMOVE_ROWS_WITH_EMPTY
                        If set, removes rows that have empty values

Assumes that the accessions are under characteristic - study to make the sample to accession link. Data files need to be available at <input-path>/<accession><suffix>
```

