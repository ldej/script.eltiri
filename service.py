import xbmc
import json
import datetime
import utils
from apiclient.discovery import build

API_KEY = "AIzaSyDevFzQh2biOeoxtf-NZTAlvshtdhcB9ZI"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


class WhatWasService(xbmc.Monitor):
    def __init__(self):
        self.dbpath = ''
        self.dbdirectory = ''
        self.sqlcon = None
        self.sqlcursor = None

        self.load_db()

    def run(self):
        while 1:
            if xbmc.abortRequested:
                return 1
            xbmc.sleep(1000)  # wait 1 second until next check if xbmc terminates
        self.exit()

    def onNotification(self, sender, method, data):
        if method == "Player.OnPlay":
            data = json.loads(data)
            item = data.get('item')
            media_type = item.get('type')

            if media_type == 'movie':
                title = item.get('title')
                if len(title) == 11 and title.find('.') == -1:
                    video_id = title

                    # YouTube
                    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

                    response = youtube.videos().list(id=video_id, parts="snippet")
                    video_title = response.get('items')[0].get('snippet').get('title')

                    video_url = "https://www.youtube.com/watch?v={0}".format(video_id)

                    string = "{0} ({1})".format(video_title, video_url)
                else:
                    string = title
            elif media_type == "song":
                string = "[{0}] {1}. {2} - {3}".format(
                     item.get('album'), item.get('track'), ', '.join(item.get('artist')), item.get('title'))
            else:
                xbmc.log("WhatWas: Unknown media type: {0}".format(media_type))
                return

            to_store = (datetime.datetime.now(), string)

            self.sqlcursor.execute("INSERT INTO records(datetime, title) VALUES (?, ?)", to_store)
            self.sqlcon.commit()

    def exit(self):
        self.sqlcon.close()

    def load_db(self):
        self.sqlcon, self.sqlcursor = utils.init_db()