from cloudshell.layer_one.core.response.resource_info.entities.port import Port


class NetscoutPort(Port):
    def __init__(self, resource_id):
        super(NetscoutPort, self).__init__(resource_id)
