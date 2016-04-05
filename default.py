import xbmcaddon
import logging
import xbmc

from service import MonitorService

logger = logging.getLogger(__name__)


addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')

xbmc.log("Starting {0} ...".format(addonname))

xbmc.sleep(1500)  # wait 1.5 seconds to prevent import-errors

try:
    MonitorService().run()
except Exception as e:
    xbmc.log(str(e))
    logger.exception(e)
