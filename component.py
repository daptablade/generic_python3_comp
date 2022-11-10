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
import os
import shutil
import subprocess
import importlib
from pathlib import Path
import requests

NAME = "generic-python3-comp|driver"
USER_FILES_PATH = os.getenv("USER_FILES_PATH")
BE_API_HOST = os.getenv("BE_API_HOST")
MYPYPI_HOST = os.getenv("MYPYPI_HOST")
COMP_NAME = os.getenv("COMP_NAME")

sys.path.append(str(Path(__file__).parents[0] / "editables"))


def setup(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    params: dict = None,
    **kwargs,
):

    print("starting setup")
    rdict = {}

    # setup empty outputs folders as required
    fpath = "editables"  # folder with user rwx permission
    dirs = []
    user_input_files = []
    if "output_directory" in params:
        output_directory = safename(params["output_directory"])
        dirs.append(fpath + "/" + output_directory)
        rdict.update({"outputs_folder_path": fpath + "/" + output_directory})
    if "user_input_files" in params:
        if not isinstance(params["user_input_files"], list):
            raise TypeError("user_input_files should be list of filename.ext strings.")
        user_input_files = [
            safename(file["filename"]) for file in params["user_input_files"]
        ]
        params["inputs_folder_path"] = fpath
        rdict.update(
            {"inputs_folder_path": fpath, "user_input_files": user_input_files}
        )

    # create empty sub-directories for userfiles
    make_dir(dirs)

    # import latest input files from pv
    if BE_API_HOST:
        get_input_files(
            ufpath=USER_FILES_PATH,
            be_api=BE_API_HOST,
            comp=COMP_NAME,
            user_input_files=user_input_files,
        )

    if MYPYPI_HOST:
        log_text = install("editables/requirements.txt", my_pypi=MYPYPI_HOST)
        print(log_text)

    # load input files
    importlib.invalidate_caches()
    user_setup = importlib.import_module("setup")
    importlib.reload(user_setup)  # get user updates

    # execute setup
    resp = user_setup.setup(inputs, outputs, partials, params)

    # basic checks
    assert isinstance(resp, dict), "User setup returned invalid response."
    if inputs:
        assert (
            "inputs" in resp
            and isinstance(resp["inputs"], dict)
            and inputs.keys() == resp["inputs"].keys()
        ), "inputs not returned or keys mutated by setup."
        rdict["inputs"] = resp.pop("inputs", None)
    if outputs:
        assert (
            "outputs" in resp
            and isinstance(resp["outputs"], dict)
            and outputs.keys() == resp["outputs"].keys()
        ), "outputs not returned or keys mutated by setup."
        rdict["outputs"] = resp.pop("outputs", None)
    if "partials" in resp:
        assert isinstance(resp["partials"], dict), "partials should be a dictionary."
        rdict["partials"] = resp.pop("partials", None)

    if "message" not in resp:
        msg = ""
    else:
        msg = resp.pop("message", None)

    if resp:  # remaining keys get saved to setup_data accessible in compute
        rdict.update(resp)

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
    if outputs and "outputs" in resp:
        assert (
            isinstance(resp["outputs"], dict)
            and outputs.keys() == resp["outputs"].keys()
        ), "outputs not returned or keys mutated by compute."
        rdict["outputs"] = resp["outputs"]
    elif "outputs" in resp:
        rdict["outputs"] = resp["outputs"]
    if partials and "partials" in resp:
        assert (
            isinstance(resp["partials"], dict)
            and partials.keys() == resp["partials"].keys()
        ), "partials not returned or keys mutated by compute."
        rdict["partials"] = resp["partials"]
    elif "partials" in resp:
        rdict["partials"] = resp["partials"]

    # check if there are parameter updates
    if any([key not in ["outputs", "partials", "message"] for key in resp]):
        # update setup_data dictionary for param connections
        for key in resp:
            if key not in ["outputs", "partials", "message"]:
                assert key in setup_data, f"illegal compute output {key}"
                rdict[key] = resp[key]

    if "message" not in resp:
        msg = ""
    else:
        msg = resp["message"]

    # save output files to the user_storage
    if BE_API_HOST:
        post_ouput_files(
            ufpath=USER_FILES_PATH,
            be_api=BE_API_HOST,
            comp=COMP_NAME,
            outpath=setup_data["outputs_folder_path"],
        )

    return (msg, rdict)


### -------------------------------------------------- UTILS


def make_dir(dirs):
    for dir in dirs:
        dir_path = Path(dir)
        if dir_path.is_dir():
            shutil.rmtree(dir_path, ignore_errors=True)
        dir_path.mkdir()


def get_input_files(ufpath, be_api, comp, user_input_files):

    headers = {"auth0token": ufpath.split("/")[-2]}
    files = ["setup.py", "compute.py", "requirements.txt"]
    if user_input_files:
        files.extend(user_input_files)

    for file in files:

        # check if input file exists
        params = {"file_name": file, "component_name": comp}
        res = requests.get(
            f"http://{be_api}/be-api/v1/checkfilesexist",
            headers=headers,
            params=params,
        )
        res.raise_for_status()
        rdict = res.json()

        if rdict["response"]:
            # if file exists, then download it from server
            params = {"file": file, "component_name": comp, "subfolder": "inputs"}
            res = requests.get(
                f"http://{be_api}/be-api/v1/getfiles",
                headers=headers,
                params=params,
            )
            res.raise_for_status()  # ensure we notice bad responses

            with open(Path("editables") / comp / "inputs" / file, "wb") as fd:
                for chunk in res.iter_content(chunk_size=128):
                    fd.write(chunk)

    print("Completed loading input files.")


def install(requirements_path, my_pypi):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--trusted-host",
            my_pypi,
            "-i",
            f"http://{my_pypi}/simple",
            "-r",
            requirements_path,
        ],
        stdout=subprocess.PIPE,
    )
    return result.stdout.decode()


def safename(file):

    k = "1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-"
    return "".join(list(filter(lambda x: x in k, str(file))))


def post_ouput_files(ufpath, be_api, comp, outpath):
    headers = {"auth0token": ufpath.split("/")[-2]}

    # list all files in outpath
    p = Path(outpath).glob("**/*")
    filepaths = [x for x in p if x.is_file()]

    # post to file server one by one
    for filepath in filepaths:
        params = {
            "file_name": filepath.name,
            "component_name": comp,
            "subfolder": "outputs",
        }
        with open(filepath, "rb") as f:
            try:
                res = requests.post(
                    f"http://{be_api}/be-api/v1/uploadfile",
                    headers=headers,
                    files={"file": ("", f, "application/octet-stream", {})},
                    data=params,
                )
                res.raise_for_status()  # ensure we notice bad responses
            except Exception as e:
                raise requests.exceptions.HTTPError(res.text)

        # catch failed file checks on server (e.g. for .py and requirements.txt files)
        if "filesaved" in res and res["filesaved"] == False:
            raise ValueError(
                f"Could not save file {str(filepath)}. Failed checks: {str(res['failed_checks'])}"
            )
