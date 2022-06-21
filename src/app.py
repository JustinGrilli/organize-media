import os
import yaml
from tkinter import *

from screens import FreshStartup, Main
from components.data import CONFIG, user_settings_template
from components import TitleBar


SETTINGS_PATH = 'settings/config.yaml'
SCREENS = {
    'fresh_startup': FreshStartup,
    'main': Main,
}


class OrganizeMedia(Tk):
    """ Utility GUI Tool, used to rename and organize media files -
        such as Movies and TV Shows - into appropriate folders. """

    def __init__(self):
        Tk.__init__(self)
        self.overrideredirect(True)
        # self.attributes('-toolwindow', 'True')
        # self.wm_attributes('-type', 'splash')
        self.config(bg=CONFIG.colors.main)
        self.geometry(CONFIG.geometry)
        self.iconbitmap('Images/toolbar_icon.ico')
        self.settings = self.__get_user_settings()
        # Title Bar
        tb = TitleBar(self, bg=CONFIG.colors.sub, fg=CONFIG.colors.font, font=CONFIG.fonts.xxsmall,
                      bd=1, relief=RIDGE)
        tb.pack(side=TOP, fill=X)
        # Screen
        dl_path = self.settings['paths'].get('downloads')
        media_path = self.settings['paths'].get('media')
        if not dl_path or not media_path:
            self.screen = FreshStartup(self)
        else:
            self.screen = Main(self)
        self.screen.pack(fill=BOTH, expand=True)
        self.bind('<Map>', self.__on_maximize)

    def __on_maximize(self, event):
        self.state('normal')
        self.overrideredirect(True)

    def minimize(self):
        self.state('withdrawn')
        self.overrideredirect(False)
        self.iconify()

    @staticmethod
    def __get_user_settings():
        # Initialize user settings if they don't exist
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        if not os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, 'w') as c:
                yaml.dump(user_settings_template, c, indent=2)

        with open(SETTINGS_PATH) as file:
            settings = yaml.safe_load(file)
        return settings

    def change_screen(self, next_screen):
        """
        Args:
            next_screen (str):
        """

        self.screen.pack_forget()
        self.screen.destroy()
        self.screen = SCREENS[next_screen](self)
        self.screen.pack(fill=BOTH, expand=True)


app = OrganizeMedia()
app.mainloop()
