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
        CREATE_MACHINE_MAP = {
            subclass.__name__.lower(): subclass
            for subclass in cls.__subclasses__()
        }
        machine_family = Machine._get_machine_family(short_name=short_name)
        return CREATE_MACHINE_MAP[machine_family](short_name)

    @staticmethod
    def _get_machine_family(short_name: str) -> str | None:
        MACHINE_FAMILY_MAP: dict[str, str] = {}
        for family, machine_dicts in machines.items():
            for machine in machine_dicts.keys():
                MACHINE_FAMILY_MAP[machine] = family

        if MACHINE_FAMILY_MAP is None:
            raise Exception(f'Error getting machine family: {short_name}.')

        return MACHINE_FAMILY_MAP[short_name]

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


class Swab(Machine):
    def __init__(self: Swab, machine_id: str) -> None:
        self.short_name = machine_id
        self.name = self.short_name.replace('swab', 'Swab Poucher ')
        self.id = self.short_name.replace('swab', '')

    def __repr__(self: Swab) -> str:
        return self.short_name
