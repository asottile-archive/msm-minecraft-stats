import datetime
import gzip
import os
import re

from collections import namedtuple

# Intended for use with MSM

ARCHIVES_PATH = '/opt/msm/archives/logs/herpderp/'

DATE_LENGTH = 19
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

MINECRAFT_IDENTIFIER = '[A-Za-z0-9_]+'
IP_AND_PORT = '\d+\.\d+\.\d+\.\d+:\d+'
DECIMAL = '-?\d+\.\d+'

# Matches:
#    {1} - INFO / etc.
#    {2} - Line text.
LINE_MATCH_REGEX = re.compile('^\[([A-Z]+)\] (.*)$')

LOGIN_REGEX = re.compile(
    '^(' + MINECRAFT_IDENTIFIER + ')' +
    '\[/(' + IP_AND_PORT + ')\] ' +
    'logged in with entity id \d+ at ' +
    '\((' + DECIMAL + '), (' + DECIMAL + '), (' + DECIMAL + ')\)$'
)

LOGOUT_REGEX = re.compile('(' + MINECRAFT_IDENTIFIER + ') lost connection: (.*)$')

MESSAGE_REGEX = re.compile('<(' + MINECRAFT_IDENTIFIER + ')> (.*)$')

SERVER_COMMAND_REGEX = re.compile('\[(' + MINECRAFT_IDENTIFIER + '): ([^\]]+)\]')

INFO = 'INFO'
WARNING = 'WARNING'

SAVING_MESSAGES = [
    'Turned off world auto-saving',
    'Turned on world auto-saving',
    'Saving...',
    'Saved the world',
]

CANT_KEEP_UP_MESSAGE = "Can't keep up! Did the system time change, or is the server overloaded?"
MOVED_WRONGLY_MESSAGE = ' moved wrongly!'
FLOATING_TOO_LONG_MESSAGE = ' was kicked for floating too long!'

Coordinate = namedtuple('Coordinate', ['x', 'y', 'z'])

class DataHolder:
    def __init__(self, value=None, attr_name='value'):
        self._attr_name = attr_name
        self.set(value)
    def __call__(self, value):
        return self.set(value)
    def set(self, value):
        setattr(self, self._attr_name, value)
        return value
    def get(self):
        return getattr(self, self._attr_name)

class LogLine:

    original_line_text = ''
    date = None
    message_type = ''
    message_text = ''

    user = None

    # INFO ones
    is_saving_message = False

    is_login = False
    login_ip_and_port = None
    login_coordinate = None

    is_logout = False
    logout_reason = None

    is_chat = False
    chat_message = None

    # WARNING ones
    is_moved_wrongly = False
    is_cant_keep_up = False
    is_floating_too_long = False

    # Defaults
    is_unknown = False

    def __init__(self, line_text):

        self.original_line_text = line_text

        # Parse date out of line.
        self.date = datetime.datetime.strptime(
            line_text[:DATE_LENGTH:],
            DATE_FORMAT
        )

        no_date_string = line_text[DATE_LENGTH + 1::]

        line_matches = LINE_MATCH_REGEX.match(no_date_string)

        # A string like 'INFO' or 'WARNING'
        self.message_type = line_matches.groups()[0]
        self.message_text = line_matches.groups()[1]

        if self.message_type == INFO:

            last_regex = DataHolder()

            if self.message_text in SAVING_MESSAGES:
                self.is_saving_message = True
            elif last_regex(LOGIN_REGEX.match(self.message_text)):
                self.is_login = True
                self.user = last_regex.value.groups()[0]
                self.login_ip_and_port = last_regex.value.groups()[1]
                self.login_coordinate = Coordinate(
                    float(last_regex.value.groups()[2]),
                    float(last_regex.value.groups()[3]),
                    float(last_regex.value.groups()[4])
                )
            elif last_regex(LOGOUT_REGEX.match(self.message_text)):
                self.is_logout = True
                self.user = last_regex.value.groups()[0]
                self.logout_reason = last_regex.value.groups()[1]
            elif last_regex(MESSAGE_REGEX.match(self.message_text)):
                self.is_chat = True
                self.user = last_regex.value.groups()[0]
                self.chat_message = last_regex.value.groups()[1]
            elif last_regex(SERVER_COMMAND_REGEX.match(self.message_text)):
                self.is_server_command = True
                self.user = last_regex.value.groups()[0]
                self.server_command_text = last_regex.value.groups()[1]
            else:
                is_unknown = True

        elif self.message_type == WARNING:

            if self.message_text.endswith(MOVED_WRONGLY_MESSAGE):
                # Message is like '%player moved wrongly!'
                self.is_moved_wrongly = True
                self.user = self.message_text[:-1 * len(MOVED_WRONGLY_MESSAGE):]
            elif self.message_text == CANT_KEEP_UP_MESSAGE:
                self.is_cant_keep_up = True
            elif self.message_text.endswith(FLOATING_TOO_LONG_MESSAGE):
                # Message is like '%player was kicked for floating too long!
                self.is_floating_too_long = True
                self.user = self.message_text[:-1 * len(FLOATING_TOO_LONG_MESSAGE):]
            else:
                raise NotImplementedError('Unknown warning.')

        else:
            raise NotImplementedError('Unknown message type.')

    def __repr__(self):
        return self.original_line_text

def get_all_log_lines():
    """Collects the msm stats for archived logs."""

    for log_file in os.listdir(ARCHIVES_PATH):
        with gzip.open(ARCHIVES_PATH + log_file) as gzip_log:
            for line in gzip_log:
                line = line.strip()

                # Files start with a prefix.
                if not line.startswith('Previous logs can be found at '):
                    yield LogLine(line)
