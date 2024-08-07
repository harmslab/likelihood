import pytest

import dataprob

import pandas as pd
import numpy as np
import os, json, pickle


@pytest.fixture(scope="module")
def binding_curve_test_data():
    """
    Main set of binding test data for testing fits.
    """

    # Find directory with test files
    base_dir = os.path.dirname(os.path.abspath(__file__))
    example_dir = os.path.abspath(os.path.join(base_dir,"examples"))

    # Load json describing test informations
    json_file = os.path.join(example_dir,"binding-curves.json")
    json_data = json.load(open(json_file,"r"))

    # Load csv with fit edata
    test_file = json_data["test_file"]
    f = os.path.join(example_dir,test_file)
    json_data["df"] = pd.read_csv(f,index_col=0)

    # ------------------------------------------------------------
    # Generic method that can be fit (observable takes a single
    # numpy array of arguments and returns an array of y_calc)
    # ------------------------------------------------------------
    class BindingCurve:
        """
        Pre-wrapped binding model.
        """
        def __init__(self,X):
            self.X = X
        def observable(self,K):
            return K[0]*self.X/(1 + K[0]*self.X)

    lm = BindingCurve(X=json_data["df"].X)
    json_data["generic_model"] = lm.observable

    # ------------------------------------------------------------
    # Save a model that should be readily wrapped by ModelWrapper
    # ------------------------------------------------------------

    def wrappable_model(K=1,df=None):
        """
        A form of the model that should be wrappable by ModelWrapper.
        """
        return K*df.X/(1 + K*df.X)

    json_data["wrappable_model"] = wrappable_model

    def model_to_test_wrap(K1,K2=20,extra_stuff="test",K3=42):

        K1 = float(K1)
        K2 = float(K2)
        K3 = float(K3)

        return K1*K2*K3

    json_data["model_to_test_wrap"] = model_to_test_wrap

    return json_data

@pytest.fixture(scope="module")
def fit_tolerance_fixture():
    """
    Fit tolerance for checking (relative tolerance)
    """
    return 0.1

@pytest.fixture(scope="module")
def fitter_object(binding_curve_test_data):
    """
    Do a successful fit that can be passed into other functions
    """

    out_dict = {}

    # Do a generic fit where the input function (generic_model) is run without
    # an intervening ModelWrapper

    generic_fit = dataprob.MLFitter()

    model = binding_curve_test_data["generic_model"]
    guesses = binding_curve_test_data["guesses"]
    df = binding_curve_test_data["df"]

    generic_fit.fit(model=model,
                    guesses=guesses,
                    y_obs=df.Y)

    if not generic_fit.success:
        raise RuntimeError("generic test fit did not converge!")

    out_dict["generic_fit"] = generic_fit

    # Do a fit where the input function is wrapped by ModelWrapper

    wrapped_fit = dataprob.MLFitter()
    
    model = binding_curve_test_data["wrappable_model"]
    model = dataprob.ModelWrapper(model)
    df = binding_curve_test_data["df"]
    model.df = df

    guesses = binding_curve_test_data["guesses"]
    

    wrapped_fit.fit(model=model,
                    guesses=guesses,
                    y_obs=df.Y)
    
    if not wrapped_fit.success:
        raise RuntimeError("wrapped test fit did not converge!")

    out_dict["wrapped_fit"] = wrapped_fit


    return out_dict

## Code for skipping slow tests.

def pytest_addoption(parser):
    parser.addoption("--runslow",
                     action="store_true",
                     default=False,
                     help="run slow tests")

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
