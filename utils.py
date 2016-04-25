import os
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import sqlite3
import xbmc
import xbmcgui
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


def send_test_email():
    test_message = "A test email to check if the SMTP email settings are correct."
    send_mail(
        test_message,
        test_message,
        recipients=[(addon.getSetting('smtp_from_name'), addon.getSetting('smtp_from_email'))]
    )


def send_mail(payload_html, payload_plain, recipients=None):
    # Recipients should be a list of tuples [(name, email), ...]

    message = MIMEMultipart('alternative')

    sender_email = addon.getSetting('smtp_from_email')
    sender_name = addon.getSetting('smtp_from_name')

    message["Subject"] = "A list of things we played"
    message["From"] = email.utils.formataddr((sender_name, sender_email))
    message["To"] = ", ".join([email.utils.formataddr(recipient) for recipient in recipients])

    part_plain = MIMEText(payload_plain, 'plain')
    part_html = MIMEText(payload_html, 'html')

    message.attach(part_plain)
    message.attach(part_html)

    encoding = addon.getSetting('smtp_encryption')
    server = addon.getSetting('smtp_server')
    port_map = {'None': 25, 'SSL/TLS': 465, 'STARTTLS': 587}
    port = port_map[encoding]
    username = addon.getSetting('smtp_username')
    password = addon.getSetting('smtp_password')

    try:
        if encoding == 'STARTTLS':
            connection = smtplib.SMTP(server, port)
            connection.ehlo()
            connection.starttls()
        elif encoding == 'SSL/TLS':
            connection = smtplib.SMTP_SSL(server, port)
            connection.ehlo()
        else:
            connection = smtplib.SMTP(server, port)

        connection.login(username, password)
        connection.sendmail(sender_email, [r[1] for r in recipients], message.as_string())
        connection.close()
    except Exception as exception:
        xbmc.log(str(exception))
        xbmcgui.Dialog().notification(
            addonname, "Sending email failed: {0}".format(str(exception)), xbmcgui.NOTIFICATION_ERROR)

    xbmcgui.Dialog().notification(addonname, "Email sent successfully!")
    return


def construct_plain_payload(records):
    return "This is what we played:\n\n" + "\n".join(
        ["{0}: {1}".format(record[0].strftime("%H:%M:%S"), record[1]) for record in records])


def construct_html_payload(records):
    record_list = "\n".join(
        ["<li>{0}: {1}</li>".format(record[0].strftime("%H:%M:%S"), record[1]) for record in records])
    return """
<html>
  <head></head>
  <body>
    <p>This is what we played:<p>
    <ol>
      {0}
    </ol>
  </body>
</html>
""".format(record_list)
