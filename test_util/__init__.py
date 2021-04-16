import os

def get_test_path():
    """Returns test data path"""
    path, name = os.path.split(__file__)
    return os.path.join(path,"..", 'test-data')

def get_test_fname(fname):
    """Returns test data filename"""
    path = get_test_path()
    full_path = os.path.join(path, fname)
    return full_path