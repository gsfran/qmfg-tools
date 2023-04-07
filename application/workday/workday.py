# import json
# from dataclasses import dataclass
# from datetime import date, time

# from machines import *


# @dataclass
# class WorkDay:
#     """
#     A single day of production. 
#     """
#     date: date
#     start_time: time = time(6)
#     end_time: time = time(6)

#     def __post_init__(self) -> None:
#         self.load_machines()

#     ## ADD SHIFT_TIMES.JSON AND __POST_INIT__()
    
#     def load_machines(self) -> None:

#         file = './machines/machines.json'

#         with open(file, 'r') as reader:
#             self.machines = json.load(reader)

#         for machine_name, machine_info in self.machines.items():
#             if machine_info['family'] == 'itrak':
#                 machine_info['object'] = iTrak(machine_info)