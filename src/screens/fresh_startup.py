import math
import os
import yaml
from tkinter import *

from src.components.ui import Buttons
from src.funcs.user_configuration import save_paths
from src.components.data import CONFIG, Paths


class FreshStartup(Frame):
    def __init__(self, app, bg=CONFIG.colors.main, *args, **kwargs):
        """
        Args:
            app (Tk):
        """
        Frame.__init__(self, app, bg=bg, *args, **kwargs)
        app.geometry('400x400+%s+%s' % (
            math.floor(self.winfo_screenwidth() / 2 - 200),
            math.floor(self.winfo_screenheight() / 2 - 200)
        ))
        buttons = Buttons()
        lbl1 = Label(self, text='Welcome,', bg=bg, fg=CONFIG.colors.alt, font=CONFIG.fonts.xxlarge)
        lbl2 = Label(self, text='Start by locating your media', wraplength=450,
                     bg=CONFIG.colors.main, fg=CONFIG.colors.special_alt, font=CONFIG.fonts.xlarge)
        b = buttons.select_media(self)
        b.config(
            command=lambda x=app: self.on_select_media(x),
            bd=1,
            relief=RAISED
        )

        lbl1.pack(fill=X, pady=30)
        b.pack()
        lbl2.pack(fill=X, pady=30)

    @staticmethod
    def on_select_media(app):
        """
        Args:
            app (Tk):
        """
        os.makedirs(os.path.dirname(CONFIG.settings_path), exist_ok=True)
        if not os.path.exists(CONFIG.settings_path):
            with open(CONFIG.settings_path, 'w') as c:
                user_settings = {
                    'media_extensions': CONFIG.media_extensions,
                    'paths': CONFIG.paths.to_dict()
                }
                yaml.dump(user_settings, c, indent=2)

        settings = save_paths(CONFIG.settings_path)
        missing_path = False
        for name, path in settings.items():
            if not path:
                missing_path = True
        if not missing_path:
            CONFIG.paths = Paths(**settings['paths'])
            app.change_screen('main')
