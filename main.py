#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reddit Twitch Stream Notifier

Changelog
v1:
Initial release, will check a twitch stream and post to a specified subreddit upon going live.
Post will be removed on going offline.

vFuture:
Add logging to subreddit wiki?
Add a command toggle, allowing mods of the subreddit to message the bot and force the bot to stop posting.
    In this case, a message would be sent to the bot's manager informing them that this has occurred.

Released under the MIT License
"""

# Imports
# Built in packages.
import configparser
import sqlite3

# Non-standard packages.
import requests
import praw



"""
Config Loading
"""
config = configparser.ConfigParser()
config.read('config.ini')
_CLIENT_ID = config['TWITCH']['Client-ID']  # Client-ID for Twitch Requests
_CHANNEL = config['TWITCH']['Channels']  # Channel to Check
_SUBREDDIT = config['REDDIT']['Subreddit']  # Channel to Check



"""
Initial Configuration Check
"""
def check_config():
    """
    Check each configuration value exists, else print a warning and abort the script.
    Then connect to the database and if necessary, perform an initial setup.
    """
    # Check config is not empty.
    if len(_CLIENT_ID) == 0:
        print('Error: Missing value for Client-ID in config.ini')
        raise SystemExit
    if len(_CHANNEL) == 0:
        print('Error: Missing value for Channel in config.ini')
        raise SystemExit
    if len(_SUBREDDIT) == 0:
        print('Error: Missing value for Subreddit in config.ini')
        raise SystemExit

    # Setup .db if not already setup.
    conn = sqlite3.connect('Posts.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS History (Title TEXT NOT NULL, Game_ID TEXT NOT NULL, Started_At TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS Last_Status (timestamp TEXT NOT NULL UNIQUE)')
    c.execute('CREATE TABLE IF NOT EXISTS Last_Post (submission_id TEXT NOT NULL UNIQUE)')
    conn.commit()
    conn.close()



"""
Twitch Functions
"""
def get_user_id():
    """
    Take the Display Name of a Twitch channel and find the associated User ID, which the new API version uses.
    Documentation is at https://dev.twitch.tv/docs/v5/#translating-from-user-names-to-user-ids
    Requires a ClientID from Twitch.

    :return: string - The User ID matching the supplied Display Name.
    """
    url = f'https://api.twitch.tv/kraken/users?login={_CHANNEL}'
    headers = {'Accept': 'application/vnd.twitchtv.v5+json',  # Ask for a return from the V5 API, not the live version.
               'Client-ID': _CLIENT_ID}
    print(f'Requesting User ID for {_CHANNEL} from Twitch... ', end='')
    request = requests.get(url, headers=headers)
    print(f'Done!')
    user_id = request.json()
    return user_id['users'][0]['_id']


def get_live_status(user_id):
    """
    Take the User ID of a Twitch channel and request any current streams.
    Documentation is at: https://dev.twitch.tv/docs/api/reference#get-streams

    :param user_id: The User ID of the channel that is being checked.
    :return: dict - The JSON object for the currently active stream.
                    If the channel is offline, the IndexError will return a NoneType.
    """
    url = f'https://api.twitch.tv/helix/streams?user_id={user_id}'
    headers = {'Client-ID': _CLIENT_ID}
    print(f'Requesting current streams for user {_CHANNEL} (ID {user_id})... ', end='')
    request = requests.get(url, headers=headers)
    print(f'Done!\n')
    streams = request.json()
    try:
        return streams['data'][0]
    except IndexError:
        return None



"""
Reddit Functions
"""
def reddit_authenticate():
    """
    Uses a praw.ini file in the working directory.
    Documentation is at https://praw.readthedocs.io/en/latest/getting_started/authentication.html

    :return: object - The base authenticated instance to be used in the script.
    """
    print('Authenticating with Reddit... ', end='')
    reddit = praw.Reddit('Main')
    print(f'Done!')
    return reddit


def post_to_subreddit(title, link, reddit):
    """
    Submit a post to reddit containing the link to the Twitch channel.

    :param title: The title of the stream, prepended with "Live Now".
    :param link: The link to the Twitch channel.
    :param reddit: The authenticated reddit instance.
    :return: string - The id of the submitted thread, used to later delete the thread.
    """
    print(f'Submitting to {_SUBREDDIT}: Title: {title}... ', end='')
    submission = reddit.subreddit(_SUBREDDIT).submit(title=title, url=link, resubmit='True', send_replies=False)
    print(f'Done!')
    return submission.id


def delete_post(submission_id, reddit):
    """
    If the stream has gone offline, delete the discussion thread.
    TODO: Save thread permalink for later reference in subreddit wiki?

    :param submission_id: The id of the previously submitted thread.
    :param reddit: The authenticated reddit instance.
    """
    print(f'Deleting submission {submission_id}... ', end='')
    thread = reddit.submission(submission_id)
    thread.delete()
    print(f'Done!')



"""
Other Functions
"""
def check_switch():
    """
    Retrieve the started_at timestamp of the previous script run.

    :return: string - The starting time of the stream.
    """
    conn = sqlite3.connect('Posts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM Last_Status')
    timestamp = c.fetchall()
    conn.commit()
    conn.close()
    if not timestamp:
        return None
    print(f'Previous timestamp was {timestamp[0][0]}')
    return timestamp[0][0]


def check_post():
    """
    Retrieve the submission_id of the previously submitted thread, used to delete the thread on stream ending.

    :return: string - The submission_id of the thread to be deleted.
    """
    conn = sqlite3.connect('Posts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM Last_Post')
    submission_id = c.fetchall()
    conn.commit()
    conn.close()
    if not submission_id:
        return None
    print(f'Previous submission_id was {submission_id[0][0]}')
    return submission_id[0][0]


def save_switch(started_at):
    """
    Save the started_at timestamp of the previous script run.

    :param started_at: The starting time of the stream.
    """
    conn = sqlite3.connect('Posts.db')
    print('Saving stream starting time')
    c = conn.cursor()
    c.execute("SELECT * FROM Last_Status")
    found = c.fetchone()
    if found == [] or found is None:
        c.execute("INSERT INTO Last_Status VALUES(?)", (started_at,))
    else:
        c.execute("DELETE FROM Last_Status")
        c.execute("INSERT INTO Last_Status VALUES(?)", (started_at,))
    conn.commit()
    conn.close()


def save_post(submission):
    """
    Save the submission_id of the submitted thread, used to later delete the thread on stream ending.

    :param submission: The submission_id of the thread to be deleted.
    """
    conn = sqlite3.connect('Posts.db')
    print('Saving submission_id')
    c = conn.cursor()
    c.execute("SELECT * FROM Last_Post")
    found = c.fetchone()
    if found == [] or found is None:
        c.execute("INSERT INTO Last_Post VALUES(?)", (submission,))
    else:
        c.execute("DELETE FROM Last_Post")
        c.execute("INSERT INTO Last_Post VALUES(?)", (submission,))
    conn.commit()
    conn.close()


def save_info(title, game_id, started_at):
    """
    Save information about the current stream, useful for later debugging.

    :param title: The title of the stream.
    :param game_id: The id of the game being played (this appears to be an internal Twitch id).
    :param started_at: The starting time of the stream.
    """
    conn = sqlite3.connect('Posts.db')
    print('Saving stream info')
    c = conn.cursor()
    c.execute("SELECT * FROM History WHERE Started_At = ?", (started_at,))
    found = c.fetchone()
    if found == [] or found is None:
        c.execute("INSERT INTO History VALUES(?, ?, ?)", (title, str(game_id), started_at))
    conn.commit()
    conn.close()


def clear_database():
    """
    After deleting the post, clear the database for next use.
    """
    conn = sqlite3.connect('Posts.db')
    print('Deleting old info')
    c = conn.cursor()
    c.execute("DELETE FROM Last_Status")
    c.execute("DELETE FROM Last_Post")
    conn.commit()
    conn.close()



# Main Function, called when running from file
def run_bot():
    # Test Config and .db are set up
    check_config()

    # Check twitch account for streams
    user_id = get_user_id()
    stream = get_live_status(user_id)

    # If stream is active but the type is not live, it will be streaming old VODs
    if stream is not None and stream['type'] != 'live':
        raise SystemExit

    # Get the status at previous runtime (Live/Not Live)
    previous = check_switch()

    # If no stream and there was no stream on the previous run, quit.
    if stream is None and previous is None:
        print(f'Stream is offline and was not online in the previous run, aborting.')
        raise SystemExit

    # If stream is live and the timestamp matches the previous run, quit.
    elif stream is not None and previous is not None:
        if stream['started_at'] == previous:
            print(f'Stream is online and started_at timestamp matches previous run, aborting.')
            raise SystemExit

        # If stream and a previous, but different previous, check for and delete any previous thread, then post a new thread.
        else:
            # Log in to reddit.
            reddit = reddit_authenticate()

            print('Stream appears to have restarted, deleting old thread and re-posting.')
            submission = check_post()
            if submission:
                delete_post(submission, reddit)
                clear_database()

            # Set up variables
            title = f'Live Now: {stream["title"]}'
            game_id = stream['game_id']
            started_at = stream['started_at']
            link = f'https://www.twitch.tv/{_CHANNEL}'

            submission = post_to_subreddit(title, link, reddit)
            save_post(submission)
            save_info(title, game_id, started_at)
            save_switch(started_at)

    # If only one of stream or previous is active,  either post or delete as needed.
    else:
        # Log in to reddit.
        reddit = reddit_authenticate()

        # if no stream and there is a previous thread, delete the old post and clear the stored submission id and switch.
        if stream is None:
            print('Stream has gone offline.')
            submission = check_post()
            delete_post(submission, reddit)
            clear_database()

        # If stream and no previous, post a new thread, the save the post_id, switch and stream info.
        elif previous is None:
            print('Stream has come online.')
            # Set up variables
            title = f'Live Now: {stream["title"]}'
            game_id = stream['game_id']
            started_at = stream['started_at']
            link = f'https://www.twitch.tv/{_CHANNEL}'

            submission_id = post_to_subreddit(title, link, reddit)
            save_post(submission_id)
            save_info(title, game_id, started_at)
            save_switch(started_at)


if __name__ == '__main__':
    try:
        run_bot()
    except SystemExit:
        print('Exit called.')
