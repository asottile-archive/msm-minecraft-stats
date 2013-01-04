from collections import namedtuple
from datetime import timedelta

from minecraft_stats import get_all_log_lines

PlayDuration = namedtuple('PlayDuration', ['user', 'start', 'end'])

def yield_play_durations(lines=[]):
    '''Yields tuples of play durations (user, start_time, end_time)

    Args:
        lines: optional list of supplied lines (could be filtered)
    '''
    # Get all the login and logouts and sort them by user and then date
    if not lines:
        lines = [l for l in get_all_log_lines() if l.is_login or l.is_logout]
    else:
        lines = [l for l in lines if l.is_login or l.is_logout]

    # We want to sort by user and then by date to allow us to process correctly
    lines.sort(key=lambda line: (line.user, line.date))

    login_date = None
    login_user = None

    for line in lines:
        # If user is None then we are not "logged in"
        if line.is_login and login_user is None:
            login_date = line.date
            login_user = line.user
            continue
        elif line.is_logout and login_user == line.user:
            yield PlayDuration(login_user, login_date, line.date)

        # Either we got bad data or we parsed a logout
        # Either case we clear what we had
        login_date = None
        login_user = None

def get_play_times_by_player():
    '''Gets a dict of play times by player

    {
        player_name: {
            'duration': timedelta of total play time,
            'sessions': list of tuples of (user, start, end)
        }
    }
    '''
    player_time_tuples = yield_play_durations()

    player_times = {}
    for player, start, end in player_time_tuples:
        if not player_times.has_key(player):
            player_times[player] = {
                'duration': timedelta(),
                'sessions': []
            }

        player_times[player]['duration'] += end - start
        player_times[player]['sessions'].append((player, start, end))

    return player_times

def get_play_times_by_player_by_day(play_times={}):
    '''Gets a dict of play times by player and date

    {
        player_name: {
            'duration': timedelta of total play time,
            'sessions': list of tuples of (user, start, end),
            'dates': dict, keys: date object, values: timedelta
        }
    }
    '''

    if not play_times:
        play_times = get_play_times_by_player()

    for user in play_times.keys():
        play_times[user]['dates'] = {}
        for _, start, end in play_times[user]['sessions']:
            date_key = start.date()
            if not play_times[user]['dates'].has_key(date_key):
                play_times[user]['dates'][date_key] = timedelta()
            play_times[user]['dates'][date_key] += end - start

    return play_times

def to_Ymd(date):
    return date.strftime('%Y-%m-%d')

def timedelta_to_string(delta):
    '''Returns a string like hh:mm:ss'''
    s = delta.total_seconds()
    hours = s / 3600
    minutes = s % 3600 / 60
    seconds = s % 60
    return '%02d:%02d:%02d' % (hours, minutes, seconds)

if __name__ == '__main__':
    times = get_play_times_by_player_by_day()

    total_time = timedelta()

    for player in times.keys():
        total_time += times[player]['duration']

        print player
        print 'TOTAL: ' + timedelta_to_string(times[player]['duration'])
        print 'Days Played:'

        dates_sorted = [
            date_duration for date_duration in times[player]['dates'].items()
        ]
        dates_sorted.sort()

        for date, date_duration in dates_sorted:
            print '-' * 2 + to_Ymd(date) + '.' * 12 + timedelta_to_string(date_duration)

        print '=' * 32

    print '=' * 32
    print 'OVERALL TOTAL: ' + timedelta_to_string(total_time)
