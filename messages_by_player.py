from optparse import OptionParser

from minecraft_stats import get_all_log_lines
from play_times import yield_play_durations


def get_messages_by_player(player, include_all_while_online=False):
    '''Returns all messages by player.

    Args:
        player - name of the player
        include_all_while_online - Include all messages while a player is
            online.
    '''

    all_lines = [line for line in get_all_log_lines()]
    all_lines.sort(key=lambda line: line.date)

    if include_all_while_online:
        player_durations = [d for d in yield_play_durations(all_lines)]
        player_durations = [d for d in player_durations if d.user == player]

        lines = [
            line for line in all_lines
            if bool([
                True for duration in player_durations
                if line.date >= duration.start and line.date <= duration.end
            ])
        ]
        return lines

    else:
        lines = [line for line in all_lines if line.user == player]
        return lines

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        '-i',
        '--include-conversations',
        action='store_true',
        dest='include_conversation',
        default=False,
        help='Include anything that happened while the user was online.'
    )
    opts, args = parser.parse_args()

    if len(args) != 1:
        print 'Expected player name!'
    else:
        for line in get_messages_by_player(args[0], opts.include_conversation):
            print line



