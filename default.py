import xbmcaddon
import logging
import xbmc

from service import MonitorService

logger = logging.getLogger(__name__)


addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')

xbmc.log("Starting {0} ...".format(addonname))

try:
    MonitorService().run()
except Exception as e:
    xbmc.log(str(e))
    logger.exception(e)
