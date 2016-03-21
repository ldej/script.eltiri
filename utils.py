import os

import sqlite3
import xbmc
import xbmcaddon
import xbmcvfs

__addon_id__ = u'script.whatwas'
__addon__ = xbmcaddon.Addon(__addon_id__)


def data_dir():
    """"get user data directory of this addon.
    according to http://wiki.xbmc.org/index.php?title=Add-on_Rules#Requirements_for_scripts_and_plugins
    """
    __datapath__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode('utf-8')
    if not xbmcvfs.exists(__datapath__):
        xbmcvfs.mkdir(__datapath__)
    return __datapath__


def init_db():
    dbdirectory = xbmc.translatePath(data_dir()).decode('utf-8')
    dbpath = os.path.join(dbdirectory, "whatwas.db")

    sqlcon = sqlite3.connect(dbpath, detect_types=sqlite3.PARSE_DECLTYPES)
    sqlcursor = sqlcon.cursor()

    sql = "CREATE TABLE IF NOT EXISTS records " \
          "(id INTEGER PRIMARY KEY, datetime TIMESTAMP, title TEXT, media_type TEXT, url TEXT)"
    sqlcursor.execute(sql)

    sql = "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)"
    sqlcursor.execute(sql)

    return sqlcon, sqlcursor