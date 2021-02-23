#!/usr/bin/env python

import xml.etree.ElementTree as ET
import argparse
import os.path

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument('-x', '--directory-with-configuration-files',
                        required=True,
                        help="Directory with configuration XMLs to merge"
                        )
arg_parser.add_argument('--accessions-file', required=False,
                        help="File with comma separated list of accessions to use only. "
                             "Overrides accessions list."
                        )
arg_parser.add_argument('-a', '--accessions-list', required=False,
                        help="Comma-separated list of accessions to use only."
                        )
arg_parser.add_argument('-o', '--output', required=True,
                        help="Path for output. <new-accession>-configuration.xml"
                             "will be created there."
                        )
arg_parser.add_argument('-n', '--new-accession', help='New accession for the output',
                        required=True)


def _get_test_path():
    """Returns test data path"""
    path, name = os.path.split(__file__)
    return os.path.join(path, 'test-data')

def _get_test_fname(fname):
    """Returns test data filename"""
    path = _get_test_path()
    full_path = os.path.join(path, fname)
    return full_path

def baseline_xml_configuration_skeleton():
    """
    Produces an empty XML object where additional assay groups can be added.
    For convenience, it returns the root element conf (to be dumped later into a file)
    and the assay_groups element, where additional assay groups should be added

    :return:
    """
    conf = ET.Element("configuration")
    # TODO these should be parameters
    conf.set("experimentType","rnaseq_mrna_baseline")
    conf.set("r_data","1")
    analytics = ET.SubElement(conf, "analytics")
    assay_groups = ET.SubElement(analytics, "assay_groups")

    return conf, assay_groups

def get_assay_groups(path):
    """
    Get a list of assay group elements from the specified configuration.xml file.

    :param path: to the configuration XML file.
    :return: list of all "assay_group" XML ET Elements.
    >>> assay_groups = get_assay_groups(_get_test_fname("E-MTAB-513-configuration.xml"))
    >>> len(list(assay_groups)) == 16
    True
    """
    root_ext = ET.parse(path).getroot()
    return root_ext.iter("assay_group")


def get_specified_accessions(args):
    accessions = None
    if args.accessions_file:
        with open(args.accessions_file, mode='r') as acc:
            accessions = acc.read().split(sep=",")
    elif args.accessions_list:
        accessions = args.accessions_list.split(sep=",")
    return accessions

def prepend_accession_technical_replicate(assay: ET.Element, accession):
    field = "technical_replicate_id"
    tech_rep_id = assay.get(field)
    if tech_rep_id:
        assay.set(field, f"{accession}_{tech_rep_id}")


def add_assay_groups_from_accession(path, accession, assay_groups: ET.Element, count_offset=0):
    """
    Given an accession and the path to the directory where the config XML resides,
    it traverses all its assay_group elements and adds as children to the assay_groups ET.Element.

    :param path: to the directory where the <ACCESSION>-configuration.xml file resides
    :param accession: the <ACCESSION> of the study
    :param assay_groups: ET.Element where all the assay_groups available in the XML will be stored.
    :return:
    >>> ag = ET.Element("assay_groups")
    >>> accession = "E-MTAB-2836"
    >>> path = _get_test_path()
    >>> add_assay_groups_from_accession(path, accession, ag)
    32
    >>> children = [x for x in ag]
    >>> len(children)
    32
    >>> children[28].get("label") == f"tonsil; {accession}"
    True
    """
    conf_xml_path = f"{path}/{accession}-configuration.xml"
    ag_counter = 0
    if os.path.isfile(conf_xml_path):
        for ag in get_assay_groups(conf_xml_path):
            ag.set("label", f"{ag.get('label')}; {accession}")
            ag.set("id", f"g{ag_counter+count_offset}")
            [prepend_accession_technical_replicate(assay, accession) for assay in ag]
            assay_groups.append(ag)
            ag_counter += 1
    else:
        print(f"Configuration file not found: {conf_xml_path}")
    return ag_counter


if __name__ == '__main__':
    args = arg_parser.parse_args()

    if not args.accessions_file and not args.accessions_list:
        print("Either --accessions or --accessions-file needs to be specified")

    root, assay_groups = baseline_xml_configuration_skeleton()

    assay_group_counter = 0
    for accession in get_specified_accessions(args):
        assay_group_counter += add_assay_groups_from_accession(path=args.directory_with_configuration_files,
                                                               accession=accession,
                                                               assay_groups=assay_groups,
                                                               count_offset=assay_group_counter
                                                               )

    tree = ET.ElementTree(root)
    tree.write(f"{args.output}/{args.new_accession}-configuration.xml", encoding="UTF-8", xml_declaration=True)


