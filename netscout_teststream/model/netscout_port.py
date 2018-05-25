from cloudshell.layer_one.core.response.resource_info.entities.attributes import StringAttribute, NumericAttribute
from cloudshell.layer_one.core.response.resource_info.entities.port import Port


class NetscoutPort(Port):
    """
    Netscout Port
    """
    """Netscout id:(Protocol ID, Protocol Type ID)"""
    PROTOCOL_ASSOCIATION_TABLE = {
        # SONET
        78: (10, 3),  # OC-48/STM-16
        92: (12, 3),  # OC-192/STM-64
        # Fibre Channel
        80: (38, 1),  # 1G Fibre Channel
        81: (39, 1),  # 2G Fibre Channel
        87: (40, 1),  # 4G Fibre Channel
        93: (41, 1),  # 8G Fibre Channel
        # Ethernet
        79: (30, 2),  # 1G Ethernet
        86: (30, 2),  # 1G Copper Ethernet
        90: (69, 2),  # 10G Ethernet
        99: (70, 2),  # 25G Ethernet
        97: (71, 2),  # 40G Ethernet
        100: (72, 2),  # 50G Ethernet
        98: (73, 2),  # 100G Ethernet
        # Optical
        96: (2, 0),  # Optical
        # CPRI
        102: (82, 10),  # CPRI9 (12,165.12 mbps)
        103: (81, 10),  # CPRI8 (10,137.6 mbps)
        104: (80, 10),  # CPRI7 (9,830.4 mbps)
        105: (79, 10),  # CPRI6 (6,144.0 mbps)
        106: (78, 10),  # CPRI5 (4,915.2 mbps)
        107: (77, 10),  # CPRI4 (3,072.0 mbps)
        108: (76, 10),  # CPRI3 (2,457.6 mbps)
        109: (75, 10),  # CPRI2 (1,228.8 mbp)
        110: (74, 10),  # CPRI1 (614.4 mbps)

    }
    MODEL_NAME = 'Netscout Generic L1 Port'

    def __init__(self, resource_id, port_model_name=None, netscout_protocol_id=0):
        super(NetscoutPort, self).__init__(resource_id)
        protocol_id, protocol_type_id = self.PROTOCOL_ASSOCIATION_TABLE.get(int(netscout_protocol_id), (2, 0))
        self.set_protocol(protocol_id)
        self.set_protocol_type(protocol_type_id)
        self.set_model_name(port_model_name)
        self.set_protocol_value(netscout_protocol_id)

    def set_protocol(self, value):
        if value is not None:
            self.attributes.append(NumericAttribute('Protocol', value))

    def set_protocol_type(self, value):
        if value is not None:
            self.attributes.append(NumericAttribute('Protocol Type', value))
