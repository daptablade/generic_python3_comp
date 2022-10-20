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

import time
from datetime import datetime


def compute(
    setup_data: dict = None,
    params: dict = None,
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    options: dict = None,
    root_folder: str = None,
):

    """Editable compute function."""

    # set inputs
    x = float(inputs["x"])

    # simulate user function evaluation
    fx = x + 1
    time.sleep(1)

    # set outputs
    outputs = {"fx": fx}
    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Adder compute completed."

    return {"message": message, "outputs": outputs}
