import unittest
import os
from SDRF import SDRF, SDRFEdgeColumn, TypeOfSDRFCol

TEST_SDRF_1 = os.path.join(os.path.dirname(__file__), 'sdrf_sample1.txt')
TEST_SDRF_2 = os.path.join(os.path.dirname(__file__), 'sdrf_sample2.txt')

OUT_TEST_MERGE = os.path.join(os.path.dirname(__file__), 'merged.xls')


def print_fields(entity, spaces="  "):
    print("{}{}: {}".format(spaces, entity.name, str(entity.column_data.size)))
    for sf in entity.fields:
        print_fields(sf, spaces=spaces + "  ")

class CreateSDRFTestClass(unittest.TestCase):

    def test_load(self):
        sdrf = SDRF(TEST_SDRF_1)
        for named_entity in sdrf.node_edges:
            print_fields(named_entity)

        print("***************************")

        sdrf = SDRF(TEST_SDRF_2)
        for named_entity in sdrf.node_edges:
            print_fields(named_entity)

    def test_add_block_comment(self):
        sdrf = SDRF(TEST_SDRF_1)
        sdrf.add_block_comment(node="Source Name", comment_name="Study", comment_value="E-MTABXYZ")

        assert sdrf.table.columns.get_loc("Comment[Study]") == 1

    def test_merge_characteristic(self):
        sdrf1 = SDRF(TEST_SDRF_1)
        sdrf2 = SDRF(TEST_SDRF_2)

        sdrf1.merge_external(sdrf2)

        sdrf1.table.to_csv(OUT_TEST_MERGE, sep="\t")

    def test_factor_values_at_the_end(self):
        sdrf1 = SDRF(TEST_SDRF_1)
        first_factor_value = None
        last_non_factor = None
        for i in range(len(sdrf1.node_edges)):
            if first_factor_value is None and sdrf1.node_edges[i].type == TypeOfSDRFCol.FACTOR_VALUE:
                first_factor_value = i
            elif sdrf1.node_edges[i].type != TypeOfSDRFCol.FACTOR_VALUE:
                last_non_factor = i
        assert last_non_factor < first_factor_value







