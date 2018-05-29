from collections import OrderedDict

GENERIC_ERRORS = OrderedDict([
    ("[Ii]nvalid", "Command is invalid"),
    # ("[Nn]ot [Ll]ogged", "User is not logged in"),
    ("(?<![R|r]ead) error", "Failed to perform command"),
    ("[Ss]witch\s[Nn]ot\s[Ff]ound", 'Switch name was not found')
])
