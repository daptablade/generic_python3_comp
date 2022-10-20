#    Copyright 2022 Dapta LTD

#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import sys
import importlib
from pathlib import Path

NAME = "generic_python3"
sys.path.append(str(Path(__file__).parents[0] / "editables"))


def setup(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    params: dict = None,
    **kwargs,
):

    print("starting setup")

    # import latest input files from pv

    # update python requirements

    # load input files
    importlib.invalidate_caches()
    user_setup = importlib.import_module("setup")
    importlib.reload(user_setup)  # get user updates

    # execute setup
    resp = user_setup.setup(inputs, outputs, partials, params)

    # basic checks
    assert (
        "inputs" in resp
        and isinstance(resp["inputs"], dict)
        and inputs.keys() == resp["inputs"].keys()
    ), "inputs not returned or keys mutated by setup."
    assert (
        "outputs" in resp
        and isinstance(resp["outputs"], dict)
        and outputs.keys() == resp["outputs"].keys()
    ), "outputs not returned or keys mutated by setup."

    if "message" not in resp:
        msg = ""
    else:
        msg = resp["message"]

    rdict = {"inputs": resp["inputs"], "outputs": resp["outputs"]}

    return (msg, rdict)


def compute(
    setup_data: dict = None,
    params: dict = None,
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    options: dict = None,
    root_folder: str = None,
    **kwargs,
):
    print("starting compute")

    # load input files
    importlib.invalidate_caches()
    user_compute = importlib.import_module("compute")
    importlib.reload(user_compute)  # get user updates

    # execute compute
    resp = user_compute.compute(
        setup_data, params, inputs, outputs, partials, options, root_folder
    )

    # basic checks
    rdict = {}
    assert isinstance(resp, dict), "User compute returned invalid response."
    if "outputs" in resp:
        assert (
            isinstance(resp["outputs"], dict)
            and outputs.keys() == resp["outputs"].keys()
        ), "outputs not returned or keys mutated by compute."
        rdict["outputs"] = resp["outputs"]
    if "partials" in resp:
        assert (
            isinstance(resp["partials"], dict)
            and partials.keys() == resp["partials"].keys()
        ), "partials not returned or keys mutated by compute."
        rdict["partials"] = resp["partials"]

    # check if there are parameter updates
    if any([key not in ["outputs", "partials", "message"] for key in resp]):
        # insert remaining keys into the setup_data dictionary
        for key in resp:
            if key not in ["outputs", "partials", "message"]:
                assert key in setup_data, f"illegal compute output {key}"
                rdict[key] = resp[key]

    if "message" not in resp:
        msg = ""
    else:
        msg = resp["message"]

    return (msg, rdict)
