from __future__ import annotations

import os
import json
from typing import Self, Type

with open(os.environ['MACHINES_JSON'], 'r') as machines_json:
    machines: dict[str, dict[str, bool]] = json.load(machines_json)


class Machine:

    @classmethod
    def create(cls: Type[Self], machine_type: str, machine_id: str) -> Machine:
        MACHINE_TYPE_MAP = {
            subclass.__name__.lower(): subclass
            for subclass in cls.__subclasses__()
        }
        return MACHINE_TYPE_MAP[machine_type](machine_id)


class iTrak(Machine):
    def __init__(self: iTrak, machine_id: str):
        self.id = machine_id


class Dipstick(Machine):
    def __init__(self: Dipstick, machine_id: str):
        self.id = machine_id
