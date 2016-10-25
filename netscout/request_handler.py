from common import request_handler
from common.xml_wrapper import XMLWrapper


class NetscoutRequestHandler(request_handler.RequestHandler):
    """Extend base request_handler.RequestHandler class with additional driver actions"""

    def logout(self, command_node, xs_prefix='', command_logger=None):
        """
        <Commands xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <Command CommandName="Logout" CommandId="567f4dc1-e2e5-4980-b726-a5d906c8679b">
            </Command>
        </Commands>
        """
        command_logger.info(XMLWrapper.get_string_from_xml(command_node))
        return self._driver_handler.logout(command_logger)

    def map_tap(self, *args, **kwargs):
        raise NotImplementedError
