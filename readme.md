# Reddit - Twitch Stream Notifier 

Designed to check a twitch channel and post to a subreddit upon going live. The specific brief was:  
_"Would it be possible to have the bot also notify the sub when we go live on Twitch?"_

## Installation
##### Initial Setup
Rename the example .ini files, removing the "example_" from each filename, the fill them in with the appropriate credentials.  
* For the Twitch Client_ID, see [the Twitch API docs.](https://dev.twitch.tv/docs/api/)
* For Reddit authentication credentials, see [the PRAW docs.](https://praw.readthedocs.io/en/latest/getting_started/authentication.html#password-flow), specifically the "Password Flow"

##### Code Requirements
The script runs on Python 3, and makes use of two non-standard packages:
* PRAW (v6.2.0)
* Requests (v2.22.0)

##### Running The Script
I'm running the script on a Google Cloud Compute Engine instance, specifically an f1-micro (the "always-free" instance.)  
Once the script is on the instance, set up a crontab to automatically run it every 5 minutes.

## Usage

Once set up, the script will monitor a specified Twitch channel, and act according to its status:  

* If the stream has gone live since last running:
    * Create a new post in the subreddit, with the title of the stream.
* If the stream has gone offline since last running:
    * Delete the previous thread.
* If the stream is live and was previously, but the start time has changed:
    * Delete the old thread and post a new one with the new stream details.

Otherwise, if the status of the stream has not changed from the last run, abort the script.

## Release History

* v1.0
    * Initial release, including documentation and example config files.
* v0.1
    * Work in progress, creating the github project.

## Meta

Sean Titmarsh – [/u/seantitmarsh](https://reddit.com/u/seantitmarsh)

Distributed under the MIT license. See ``LICENSE`` for more information.
