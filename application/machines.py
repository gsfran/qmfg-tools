from __future__ import annotations

import os
import json
from typing import Type

with open(os.environ['MACHINES_JSON'], 'r') as machines_json:
    machines: dict[str, dict[str, bool]] = json.load(machines_json)


class Machine:

    short_name: str
    name: str
    id: str

    @classmethod
    def create(cls: Type, machine_type: str, short_name: str) -> Machine:
        MACHINE_TYPE_MAP = {
            subclass.__name__.lower(): subclass
            for subclass in cls.__subclasses__()
        }
        return MACHINE_TYPE_MAP[machine_type](short_name)

    def __repr__(self: Machine) -> str:
        ...


class iTrak(Machine):
    def __init__(self: iTrak, machine: str) -> None:
        self.short_name = machine
        self.name = self.short_name.replace('line', 'Line ')
        self.id = self.short_name.replace('line', '')

    def __repr__(self: iTrak) -> str:
        return self.short_name


class Dipstick(Machine):
    def __init__(self: Dipstick, machine_id: str) -> None:
        self.short_name = machine_id
        self.name = self.short_name.replace('dipstick', 'Dipstick ')
        self.id = self.short_name.replace('dipstick', '')

    def __repr__(self: Dipstick) -> str:
        return self.short_name
