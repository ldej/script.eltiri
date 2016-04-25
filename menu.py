# -*- coding: latin-1 -*-

import re
import sys

import datetime
import xbmc
import xbmcaddon
import xbmcgui

import utils

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')


class Menu:
    def __init__(self):
        self.sqlcon, self.sqlcursor = utils.init_db()
        self.history = None

    def show(self):
        while True:
            # Select category menu
            idx = xbmcgui.Dialog().select("Options", ["Email history", "Show history", "Users"])
            if idx == -1:
                break
            action = ["email_history", "history", "users"][idx]

            if action == "history":
                History(self.sqlcursor).show_menu()
            elif action == "users":
                Users(self.sqlcon, self.sqlcursor).show_menu()
            elif action == "email_history":
                EmailHistory(self.sqlcon, self.sqlcursor).show_menu()
        self.exit()

    def exit(self):
        self.sqlcon.close()


class History:
    def __init__(self, sqlcursor):
        self.sqlcursor = sqlcursor
        self.records = []
        self.record_tuples = []

        self.next_page_index = None
        self.previous_page_index = None
        self.limit = 50
        self.offset = 0

        self.len_records = self.query_len_records()
        self.number_pages = (self.len_records / self.limit) or 1

        self.current_page = 0

        self.should_break = False

    def query_len_records(self):
        return self.sqlcursor.execute("SELECT COUNT(*) FROM records").next()[0]

    def load_records(self):
        self.record_tuples = self.sqlcursor.execute(
            "SELECT records.datetime, records.title, records.media_type, records.url "
            "FROM records ORDER BY datetime DESC "
            "LIMIT {1} "
            "OFFSET {0}".format(self.offset, self.limit))
        self.record_tuples = [record for record in self.record_tuples]
        self.records = ["{0} {1}".format(record[0].strftime("%d-%m-%Y %H:%M:%S"), record[1])
                        for record in self.record_tuples]

        self.current_page = (self.offset / self.limit) + 1

        if not self.current_page == 1:
            self.previous_page_index = 0
            self.records.insert(self.previous_page_index, "<- Previous page")
        else:
            self.previous_page_index = None

        if self.len_records > self.offset + self.limit:
            self.records.append("Next page ->")
            self.next_page_index = len(self.records) - 1
        else:
            self.next_page_index = None

    def show_menu(self, on_select=None):
        if not on_select:
            on_select = self.play
        result = None

        self.load_records()
        while True:

            # Only show the select box if the fullscreen video player is not visible
            # Because we are playing video
            visibility = xbmcgui.getCurrentWindowId() == 12005
            if visibility:
                xbmc.sleep(100)
                continue
            else:
                idx = xbmcgui.Dialog().select(
                    "Played items - Page ({0}/{1})".format(self.current_page, self.number_pages), self.records)
            if idx == -1:
                self.should_break = True
            elif idx == self.next_page_index:
                self.offset += self.limit
                self.load_records()
            elif idx == self.previous_page_index:
                self.offset -= self.limit
                self.load_records()
            else:
                if self.previous_page_index is not None:
                    idx -= 1

                result = on_select(idx)

            if self.should_break:
                break
        return result

    def play(self, idx):
        timestamp, title, media_type, url = self.record_tuples[idx]

        if media_type in ["movie", "youtube"]:
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            listitem = xbmcgui.ListItem(title)
            listitem.setInfo('video', {'title': title})
            playlist.add(url=url, listitem=listitem)
            xbmc.Player().play(playlist)

            # Wait until the video is visible
            while not xbmcgui.getCurrentWindowId() == 12005:
                xbmc.sleep(100)
        elif media_type == "song":
            playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
            playlist.clear()
            listitem = xbmcgui.ListItem(title)
            listitem.setInfo('music', {'title': title})
            playlist.add(url=url, listitem=listitem)
            xbmc.Player().play(playlist)
        else:
            xbmcgui.Dialog().notification(addonname, "Don't know how to play: {0}".format(media_type))

        return False

    def records_from(self, idx):
        self.should_break = True
        records = self.record_tuples[0:idx+1]
        records.reverse()
        return records


class Users:
    def __init__(self, sqlcon, sqlcursor):
        self.sqlcon = sqlcon
        self.sqlcursor = sqlcursor
        self.users = []
        self.user_labels = []
        self.submenus = [
            ("show_users", "Show users"),
            ("add_user", "Add user"),
            ("delete_user", "Delete user"),
        ]

    def load_users(self):
        user_tuples = self.sqlcursor.execute("SELECT users.id, users.name, users.email FROM users")
        self.users = [user for user in user_tuples]
        self.user_labels = ["{0} ({1})".format(user[1], user[2]) for user in self.users]
        xbmc.log(str(self.users))

    def add_user(self):
        while True:
            name = xbmcgui.Dialog().input("Name")
            if not name:
                break
            name = name.strip()

            email_address = None
            cancel = False

            while True:
                email_input = xbmcgui.Dialog().input("Email")
                if not email_input:
                    cancel = True
                    break
                match = re.match(
                    '^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$',
                    email_input
                )
                if not match:
                    xbmcgui.Dialog().notification(addonname, "Invalid email address")
                email_address = email_input
                break

            if cancel:
                break

            result = self.sqlcursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email_address,)).next()[0]

            if result > 0:
                xbmcgui.Dialog().ok("Email already exists", "The email address already exists.")
                break

            self.sqlcursor.execute("INSERT INTO users(name, email) VALUES (?, ?)", (name, email_address))
            self.sqlcon.commit()

            xbmcgui.Dialog().notification(addonname, "Added {0} ({1}).".format(name, email_address))
            break

    def delete_user(self):
        while True:
            self.load_users()
            idx = xbmcgui.Dialog().select("Users", self.user_labels)

            if idx == -1:
                break

            user_to_delete = self.users[idx]
            xbmc.log(str(user_to_delete))
            self.sqlcursor.execute("DELETE FROM users WHERE users.id = ?", (user_to_delete[0],))
            self.sqlcon.commit()

            xbmcgui.Dialog().notification(addonname, "Deleted {0} ({1})".format(user_to_delete[1], user_to_delete[2]))

    def show_users(self):
        self.load_users()
        while True:
            idx = xbmcgui.Dialog().select("Users", self.user_labels)

            if idx == -1:
                break

    def show_menu(self):
        while True:
            idx = xbmcgui.Dialog().select(
                "Select an option", [menu[1] for menu in self.submenus]
            )
            if idx == -1:
                break

            submenu = self.submenus[idx][0]

            if submenu == "add_user":
                self.add_user()
            elif submenu == "delete_user":
                self.delete_user()
            elif submenu == "show_users":
                self.show_users()

        self.load_users()


class EmailHistory:
    def __init__(self, sqlcon, sqlcursor):
        self.sqlcon = sqlcon
        self.sqlcursor = sqlcursor

        self.users = Users(self.sqlcon, self.sqlcursor)
        self.users.load_users()

        self.records = []

        self.history_menu = [
            ("today", "Today"),
            ("today_yesterday", "Today and yesterday"),
            ("from", "From selected record until now"),
        ]

    def show_menu(self):

        while True:
            selected_users = xbmcgui.Dialog().multiselect("Select users", self.users.user_labels)
            if not selected_users:
                break
            to_email = [self.users.users[index] for index in selected_users]
            to_email = [(user[1], user[2]) for user in to_email]

            cancel = False
            while not self.records:
                idx = xbmcgui.Dialog().select("Select history", [menu[1] for menu in self.history_menu])

                if idx == -1:
                    cancel = True
                    break
                history_menu = self.history_menu[idx][0]

                if history_menu == "today":
                    self.today()
                elif history_menu == "today_yesterday":
                    self.today_yesterday()
                elif history_menu == "from":
                    self.select_from()

            if cancel:
                break

            self.send_email(to_email, self.records)
            break

    def select_from(self):
        history = History(self.sqlcursor)
        self.records = history.show_menu(on_select=history.records_from)

    def today(self):
        today = datetime.date.today()
        today = datetime.datetime(year=today.year, month=today.month, day=today.day)
        self.records = self.query_records_date(today)

    def today_yesterday(self):
        today = datetime.date.today()
        yesterday = datetime.datetime(year=today.year, month=today.month, day=today.day-1)
        self.records = self.query_records_date(yesterday)

    def query_records_date(self, today):
        record_tuples = self.sqlcursor.execute(
            """SELECT records.datetime, records.title
               FROM records WHERE records.datetime > ? ORDER BY datetime ASC""",
            (today, )
        )
        return [record for record in record_tuples]

    def send_email(self, users, records):
        result = xbmcgui.Dialog().yesno(
            "Send email?", "Do you want to send {0} records to:".format(len(records)),
            ", ".join(['{0} <{1}>'.format(user[0], user[1]) for user in users])
        )
        if result:
            utils.send_mail(utils.construct_html_payload(records), utils.construct_plain_payload(records), users)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'send_test_email':
              utils.send_test_email()
    else:
        Menu().show()
