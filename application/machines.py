from __future__ import annotations

import json
import os
from datetime import datetime as dt
from typing import Type

from application import db
from application.models import WorkOrder


def get_default_machines_from_json() -> dict[str, dict[str, bool]]:
    json_file = os.environ['MACHINES_JSON']
    with open(json_file, 'r') as j:
        default_machines: dict[str, dict[str, bool]] = json.load(j)
    return default_machines


def machine_list(machine_family: str) -> list[Machine]:
    """Returns a list of machines in the given family (e.g. 'itrak').
    Machines may be added directly to machines.json in the data folder.

    Args:
        machine_family (str): Machine family identifier

    Returns:
        list[Machine]: A list of machines under the given family.
    """
    machines = get_default_machines_from_json()
    list_: list[Machine] = [
        Machine.new_(m) for m in machines[machine_family]
    ]
    return list_


class Machine:

    short_name: str
    name: str
    id: str

    @classmethod
    def new_(cls: Type, short_name: str) -> Machine:
        SUBCLASS_MAP = {
            subclass.__name__.lower(): subclass
            for subclass in cls.__subclasses__()
        }
        machine_family = Machine._get_machine_family(short_name=short_name)
        return SUBCLASS_MAP[machine_family](short_name)

    @staticmethod
    def _get_machine_family(short_name: str) -> str | None:
        machines = get_default_machines_from_json()
        FAMILY_REVERSE_MAP: dict[str, str] = {}
        for family, machine_dicts in machines.items():
            for machine in machine_dicts.keys():
                FAMILY_REVERSE_MAP[machine] = family
        if FAMILY_REVERSE_MAP is None:
            raise Exception(f'Error getting machine family: {short_name}.')
        return FAMILY_REVERSE_MAP[short_name]

    def active_jobs(self: Machine) -> list[WorkOrder] | None:
        """Returns all currently scheduled WorkOrders.

        Returns:
            list[WorkOrder] | None: WorkOrder list
        """
        return db.session.execute(db.select(WorkOrder).where(
            WorkOrder.machine == self.short_name
        ).order_by(
            WorkOrder.priority
        )).scalars().all()

    def schedule_job(
        self: Machine, work_order: WorkOrder,
        mode: str, start_dt: dt | None,
        priority: int = -1
    ) -> None:
        MODE_MAP = {
            'replace': self._job_replace,
            'insert': self._job_insert,
            'append': self._job_append,
            'custom': self._job_custom
        }

        if work_order is None:
            raise Exception(f'No WorkOrder found: {work_order}')
        jobs = self.active_jobs()
        if jobs is None:
            jobs = []

        work_order.load_dt = dt.now()
        work_order.machine = self.short_name
        MODE_MAP[mode](work_order, jobs, start_dt)

    def _job_replace(
        self: Machine, work_order: WorkOrder,
        jobs: list[WorkOrder], start_dt: dt | None
    ) -> None:
        if jobs:
            jobs.pop(0).park()

        jobs.insert(0, work_order)
        work_order.priority = 0
        work_order.status = 'Pouching'
        work_order.pouching_start_dt = dt.now()
        work_order.log += (
            f'{self.name}: {work_order} replace scheduled for '
            f' {dt.now()}\n'
        )
        db.session.commit()

    def _job_insert(
        self: Machine, work_order: WorkOrder,
        jobs: list[WorkOrder], start_dt: dt | None
    ) -> None:

        jobs.insert(1, work_order)
        work_order.status = 'Queued'
        work_order.log += (
            f'{self.name}: {work_order} insert scheduled. {dt.now()}\n'
        )

        for job in jobs:
            job.priority = jobs.index(job)
            if job.priority == 0:
                job.status = 'Pouching'
                job.pouching_start_dt = dt.now()

        db.session.commit()

    def _job_append(
        self: Machine, work_order: WorkOrder,
        jobs: list[WorkOrder], start_dt: dt | None
    ) -> None:
        jobs.append(work_order)
        work_order.priority = jobs.index(work_order)
        if work_order.priority == 0:
            work_order.status = 'Pouching'
            work_order.pouching_start_dt = dt.now()
        else:
            work_order.status = 'Queued'
        work_order.log += (
            f'{self.name}: {work_order} append scheduled. {dt.now()}\n'
        )
        db.session.commit()

    def _job_custom(
        self: Machine, work_order: WorkOrder,
        jobs: list[WorkOrder], start_dt: dt
    ) -> None:
        for job in jobs:
            ...

    def __repr__(self: Machine) -> str:
        ...


class iTrak(Machine):
    def __init__(self: iTrak, machine: str) -> None:
        self.short_name = machine
        self.name = self.short_name.replace('line', 'Line ')
        self.id = self.short_name.replace('line', '')

    def __repr__(self: iTrak) -> str:
        return f'iTrak({self.short_name})'


class Dipstick(Machine):
    def __init__(self: Dipstick, machine_id: str) -> None:
        self.short_name = machine_id
        self.name = self.short_name.replace('dipstick', 'Dipstick ')
        self.id = self.short_name.replace('dipstick', '')

    def __repr__(self: Dipstick) -> str:
        return f'Dipstick({self.short_name})'


class Swab(Machine):
    def __init__(self: Swab, machine_id: str) -> None:
        self.short_name = machine_id
        self.name = self.short_name.replace('swab', 'Swab Poucher ')
        self.id = self.short_name.replace('swab', '')

    def __repr__(self: Swab) -> str:
        return f'Swab({self.short_name})'
