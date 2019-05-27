#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reddit Twitch Stream Notifier

Changelog
vdev:

v1:

vFuture:
"""

#Imports
# Built in packages.
import configparser
import sqlite3

# Non-standard packages.
import requests

#Constants/Config
config = configparser.ConfigParser()
config.read('config.ini')

_CLIENT_ID = config['DEFAULT']['Client-ID'] # Client-ID for Twitch Requests
_CHANNEL = config['DEFAULT']['Channels'] # Channel to Check

"""
Twitch Functions
"""
def get_user_id():
    """
    Using f-string replacement to form the url, pass the url and header (if applicable) to the requests package.
    Then use the built in .json() function, if appropriate, to return a JSON formatted object. Can also return a certain key if it has a "data" or "response" level

    :return:
    """
    url = f'https://api.twitch.tv/kraken/users?login={_CHANNEL}'
    headers = {'Accept': 'application/vnd.twitchtv.v5+json',
               'Client-ID': _CLIENT_ID}
    request = requests.get(url, headers=headers)
    user_id = request.json()
    return user_id['users'][0]['_id']


def get_live_status(user_id):
    """
    Using f-string replacement to form the url, pass the url and header (if applicable) to the requests package.
    Then use the built in .json() function, if appropriate, to return a JSON formatted object. Can also return a certain key if it has a "data" or "response" level

    :return:
    """
    url = f'https://api.twitch.tv/helix/streams?user_id={user_id}'
    headers = {'Client-ID': _CLIENT_ID}
    request = requests.get(url, headers=headers)
    streams = request.json()
    if len(streams) != 0:
        print(streams)
        return streams['data'][0]
    else:
        return 'Not Live'

"""
Reddit Functions
"""
def log_in():
    pass # TODO

def post_to_subreddit():
    pass # TODO

def update_sidebar():
    pass # TODO

def delete_post():
    pass # TODO

"""
Other Functions
"""
def check_switch():
    pass # TODO

def save_switch():
    pass # TODO

def save_info():
    pass # TODO


# Main Function, called when running from file
def run_bot():
    user_id = get_user_id()
    streams = get_live_status(user_id)
    input('')
    # TODO: Check length of streams. If 0, not live, else live.
    # TODO: Check previous run type, if matches stream case, quit.
    # TODO: Else, update and post/delete as needed, then save new switch and any info.


if __name__ == '__main__':
    try:
        run_bot()
    except SystemExit:
        print('Exit called.')
