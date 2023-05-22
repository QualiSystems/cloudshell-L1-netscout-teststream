from cloudshell.layer_one.core.response.resource_info.entities.attributes import (
    NumericAttribute,
)
from cloudshell.layer_one.core.response.resource_info.entities.port import Port


class NetscoutPort(Port):
    """Netscout Port."""

    """Netscout id:(Protocol LV, Protocol Type LV, Speed LV)"""
    PROTOCOL_ASSOCIATION_TABLE = {
        # SONET
        78: (10, 3, 21),  # OC-48/STM-16
        92: (12, 3, 22),  # OC-192/STM-64
        # Fibre Channel
        80: (38, 1, 11),  # 1G Fibre Channel
        81: (39, 1, 12),  # 2G Fibre Channel
        87: (40, 1, 13),  # 4G Fibre Channel
        93: (41, 1, 14),  # 8G Fibre Channel
        # Ethernet
        79: (30, 2, 4),  # 1G Ethernet
        86: (30, 2, 6),  # 1G Copper Ethernet
        90: (69, 2, 5),  # 10G Ethernet
        99: (70, 2, 42),  # 25G Ethernet
        97: (71, 2, 43),  # 40G Ethernet
        100: (72, 2, 44),  # 50G Ethernet
        98: (73, 2, 45),  # 100G Ethernet
        # Optical
        96: (2, 0, 1),  # Optical
        # CPRI
        102: (82, 10, 54),  # CPRI9 (12,165.12 mbps)
        103: (81, 10, 53),  # CPRI8 (10,137.6 mbps)
        104: (80, 10, 52),  # CPRI7 (9,830.4 mbps)
        105: (79, 10, 51),  # CPRI6 (6,144.0 mbps)
        106: (78, 10, 50),  # CPRI5 (4,915.2 mbps)
        107: (77, 10, 49),  # CPRI4 (3,072.0 mbps)
        108: (76, 10, 48),  # CPRI3 (2,457.6 mbps)
        109: (75, 10, 47),  # CPRI2 (1,228.8 mbps)
        110: (74, 10, 46),  # CPRI1 (614.4 mbps)
    }
    MODEL_NAME = "Netscout Generic L1 Port"

    def __init__(self, resource_id, port_model_name=None, netscout_protocol_id=0):
        super().__init__(resource_id)
        protocol_id, protocol_type_id, speed_id = self.PROTOCOL_ASSOCIATION_TABLE.get(
            int(netscout_protocol_id), (2, 0, 1)
        )
        self.set_protocol(protocol_id)
        self.set_protocol_type(protocol_type_id)
        self.set_speed(speed_id)
        self.set_model_name(port_model_name)
        self.set_protocol_value(netscout_protocol_id)

    def set_protocol(self, value):
        if value is not None:
            self.attributes.append(NumericAttribute("Protocol", value))

    def set_protocol_type(self, value):
        if value is not None:
            self.attributes.append(NumericAttribute("Protocol Type", value))

    def set_speed(self, value):
        if value is not None:
            self.attributes.append(NumericAttribute("Speed", value))
