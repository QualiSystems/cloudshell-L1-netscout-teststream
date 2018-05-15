from collections import OrderedDict

from cloudshell.cli.session.ssh_session import SSHSession
from netscout_teststream.cli.netscout_command_modes import DefaultCommandMode
from netscout_teststream.command_templates.ERRORS import GENERIC_ERRORS


class NetscoutSSHSession(SSHSession):
    def _connect_actions(self, prompt, logger):
        error_map = OrderedDict([
            ("[Aa]ccess [Dd]enied", "Invalid username/password for login"),
        ])
        error_map.update(GENERIC_ERRORS)

        action_map = OrderedDict()
        action_map['Accept/Decline'] = lambda session, logger: session.send_line("A", logger)

        prompt = DefaultCommandMode.PROMPT
        self.hardware_expect(None, expected_string=prompt, timeout=self._timeout, logger=logger,
                             action_map=action_map, error_map=error_map)
        self._on_session_start(logger)
