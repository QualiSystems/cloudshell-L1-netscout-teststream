import os
import re

from cloudshell.cli.service.cli_service import CliService

from netscout_teststream.cli.l1_cli_handler import L1CliHandler


class TestCliContextManager:
    def __init__(self, test_cli):
        self._test_cli = test_cli

    def __enter__(self):
        return self._test_cli

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class TestCliService(CliService):
    def __init__(self, data_path, logger):
        self._data_path = data_path
        self._logger = logger

    def reconnect(self, timeout=None):
        pass

    def enter_mode(self, command_mode):
        pass

    def send_command(
        self,
        command,
        expected_string=None,
        action_map=None,
        error_map=None,
        logger=None,
        *args,
        **kwargs
    ):
        self._logger.debug(command)
        file_name = re.sub(r"\*", "asterisk", command)
        file_name = re.sub(r"\s", "_", file_name)
        file_name = re.sub('"', "", file_name)

        try:
            with open(os.path.join(self._data_path, file_name + ".txt")) as f:
                output = f.read()
            return output
        except OSError:
            pass


class CLISimulator(L1CliHandler):
    def __init__(self, data_path, logger):
        super().__init__()
        self._cli_service = TestCliContextManager(TestCliService(data_path, logger))

    def get_cli_service(self, command_mode):
        return self._cli_service

    def define_session_attributes(self, address, username, password, port=None):
        pass

    def default_mode_service(self):
        return self._cli_service
