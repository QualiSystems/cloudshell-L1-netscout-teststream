from collections import OrderedDict

GENERIC_ERRORS = OrderedDict(
    [
        ("License expired!", "License expired. Please renew the license."),
        ("[Ii]nvalid", "Command is invalid"),
        ("(?<![R|r]ead) error", "Failed to perform command"),
        (r"[Ss]witch\s[Nn]ot\s[Ff]ound", "Switch name was not found"),
    ]
)
