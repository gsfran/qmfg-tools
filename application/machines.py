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
    def create(cls: Type, short_name: str) -> Machine:
        machine_family = Machine._get_machine_family(short_name=short_name)
        MACHINE_FAMILY_MAP = {
            subclass.__name__.lower(): subclass
            for subclass in cls.__subclasses__()
        }
        return MACHINE_FAMILY_MAP[machine_family](short_name)

    @classmethod
    def _get_machine_family(cls: Type, short_name: str) -> str | None:
        INVERSE_LOOKUP = {
            value_.__str__(): key_ for key_, value_ in machines.items()
        }
        return INVERSE_LOOKUP.get(short_name)

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
