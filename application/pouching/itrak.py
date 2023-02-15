from __future__ import annotations

from sqlalchemy import and_, or_

from application.vision.product_inspect import ProductInspectCamera
from application import db
from application.models import WorkOrders


class iTrak:
    """
    iTrak Production Line object.
    """
    ITRAK_DICT = {
        'Line 5': {
            'data_folder': 'Line5'
        },
        'Line 6': {
            'data_folder': 'Line6'
        },
        'Line 7': {
            'data_folder': 'Line7'
        },
        'Line 8': {
            'data_folder': 'Line8'
        },
        'Line 9': {
            'data_folder': 'Line9'
        },
        'Line 10': {
            'data_folder': 'Line10'
        }
    }

    IDEAL_RUN_RATE_HZ = 140 / 60
    STANDARD_RATE_HZ = 5000 / 3600

    def __init__(self: iTrak, line_number: str) -> None:
        self.number = line_number
        self.name = f'Line {self.number}'

        self.machine_info = iTrak.ITRAK_DICT.get(self.name)
        self.data_folder = self.machine_info.get('data_folder')

        self.product_inspect = ProductInspectCamera(self.machine_info)

    @staticmethod
    def build_lines(line_numbers: list[str]) -> dict[str, str]:
        lines = {}
        for line_number in line_numbers:
            lines[line_number] = iTrak(line_number)
        return lines

    @property
    def current_jobs(self: iTrak) -> list[WorkOrders]:
        return db.session.execute(
            db.select(WorkOrders).where(
                and_(
                    or_(
                        WorkOrders.status == 'Pouching',
                        WorkOrders.status == 'Queued'
                    ),
                    WorkOrders.line == self.number
                )
            ).order_by(
                WorkOrders.add_datetime.desc()
            )
        ).scalars()
