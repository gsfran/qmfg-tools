from dataclasses import dataclass

from cameras import PrintInspectCamera, ProductInspect


@dataclass
class Poucher:
    """
    iTrak Poucher object, contains two Camera objects.
    """
    def __init__(self, machine_info: dict) -> None:
        self.machine_info = machine_info
        self.product_inspect = ProductInspect(self.machine_info)
        self.print_inspect = PrintInspectCamera(self.machine_info)