from cloudshell.cli.service.command_mode import CommandMode


class DefaultCommandMode(CommandMode):
    PROMPT = r".*=>\s*$"
    ENTER_COMMAND = ""
    EXIT_COMMAND = "exit"

    def __init__(self):
        CommandMode.__init__(self, self.PROMPT, self.ENTER_COMMAND, self.EXIT_COMMAND)


CommandMode.RELATIONS_DICT = {DefaultCommandMode: {}}
