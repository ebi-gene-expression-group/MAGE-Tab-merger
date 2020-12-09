import unittest
import os
from SDRF import TypeOfSDRFCol

class TypeOfSDRFColTestClass(unittest.TestCase):

    def test_recognize_characteristic(self):
        typeChar = TypeOfSDRFCol.get_type("Characteristics [organism part]")
        assert typeChar == TypeOfSDRFCol.CHARACTERISTICS
        typeComm = TypeOfSDRFCol.get_type("ComMent[clinical]")
        assert typeComm == TypeOfSDRFCol.COMMENT
        typeSource = TypeOfSDRFCol.get_type("Source Name")
        assert typeSource == TypeOfSDRFCol.SOURCE_NAME

    def test_subfields(self):
        assert TypeOfSDRFCol.SAMPLE_NAME.has_subfield(TypeOfSDRFCol.COMMENT)


