"""
run these tests with `pytest tests/test_something.py` or `pytest tests` or simply `pytest`
pytest will look for all files starting with "test_" and run all functions
within this file. For basic example of tests you can look at our workshop
https://github.com/rl-institut/workshop/tree/master/test-driven-development.
Otherwise https://docs.pytest.org/en/latest/ and https://docs.python.org/3/library/unittest.html
are also good support.
"""
import tracbev.__main__ as main
import tracbev.plots as plots
import tracbev.usecase as uc
import tracbev.usecase_helpers as uc_helpers
import tracbev.utility as utility


# all tracbev modules are imported and thus tested on internal import errors
def test_imports():
    assert True
