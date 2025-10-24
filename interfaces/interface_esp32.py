"""
Copyright 2023 Mattia Orlandi, Pierangelo Maria Rapa

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import struct

import numpy as np

packetSize: int = 40
"""Number of bytes in each package."""

startSeq: list[bytes | float] = [b"="]
"""
Sequence of commands (as bytes) to start the device; floats are
interpreted as delays (in seconds) between commands.
"""

stopSeq: list[bytes | float] = [b":"]
"""
Sequence of commands (as bytes) to stop the device; floats are
interpreted as delays (in seconds) between commands.
"""

sigInfo: dict = {"sig1": {"fs": 500, "nCh": 1}}
"""Dictionary containing the signals information."""



def decodeFn(data: bytes) -> dict[str, np.ndarray]:

    dataTmp = np.array(struct.unpack(f"{len(data)//4}I", data), dtype=np.float32)

    if dataTmp.size > 0:
        dataTmp = dataTmp.reshape(-1, 1)
    else:
        return

    return {"sig1": dataTmp}

