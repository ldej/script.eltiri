import xbmcaddon
import logging
import xbmc

from service import WhatWasService

logger = logging.getLogger(__name__)


addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')

xbmc.log("Starting What Was? ...")

xbmc.sleep(1500)  # wait 1.5 seconds to prevent import-errors

try:
    WhatWasService().run()
except Exception as e:
    xbmc.log(str(e))
    logger.exception(e)
