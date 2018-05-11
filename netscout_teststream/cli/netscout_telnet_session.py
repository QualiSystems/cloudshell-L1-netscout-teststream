from collections import OrderedDict

from cloudshell.cli.session.telnet_session import TelnetSession
from netscout_teststream.cli.netscout_command_modes import DefaultCommandMode
from netscout_teststream.command_templates.ERRORS import GENERIC_ERRORS


class NetscoutTelnetSession(TelnetSession):
    def _connect_actions(self, prompt, logger):
        command = 'logon {} {}'.format(self.username, self.password)
        error_map = OrderedDict([
            ("[Aa]ccess [Dd]enied", "Invalid username/password for login"),
        ])
        error_map.update(GENERIC_ERRORS)
        action_map = OrderedDict()
        action_map['Accept/Decline'] = lambda session: session.send_line("A")

        prompt = DefaultCommandMode.PROMPT

        self.hardware_expect(command, expected_string=prompt, timeout=self._timeout, logger=logger,
                             action_map=action_map, error_map=error_map)
        self._on_session_start(logger)
