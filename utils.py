import os

import sqlite3
import xbmc
import xbmcaddon
import xbmcvfs

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')


def data_dir():
    """"get user data directory of this addon.
    according to http://wiki.xbmc.org/index.php?title=Add-on_Rules#Requirements_for_scripts_and_plugins
    """
    datapath = xbmc.translatePath(addon.getAddonInfo('profile')).decode('utf-8')
    if not xbmcvfs.exists(datapath):
        xbmcvfs.mkdir(datapath)
    return datapath


def init_db():
    dbdirectory = xbmc.translatePath(data_dir()).decode('utf-8')
    dbpath = os.path.join(dbdirectory, "{0}.db".format(addonname))

    sqlcon = sqlite3.connect(dbpath, detect_types=sqlite3.PARSE_DECLTYPES)
    sqlcursor = sqlcon.cursor()

    sql = "CREATE TABLE IF NOT EXISTS records " \
          "(id INTEGER PRIMARY KEY, datetime TIMESTAMP, title TEXT, media_type TEXT, url TEXT)"
    sqlcursor.execute(sql)

    sql = "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)"
    sqlcursor.execute(sql)

    return sqlcon, sqlcursor