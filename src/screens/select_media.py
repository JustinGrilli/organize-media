import math
import os
from tkinter import *

from src.components.data import CONFIG
from src.components.ui import OMButton, CheckBox


class SelectMedia(Frame):
    def __init__(self, app,
                 bg=CONFIG.colors.main,
                 fg=CONFIG.colors.font,
                 font=CONFIG.fonts.medium,
                 *args, **kwargs):
        Frame.__init__(self, app, bg=bg, *args, **kwargs)
        app.geometry('400x400+%s+%s' % (
            math.floor(app.winfo_screenwidth() / 2 - 200),
            math.floor(app.winfo_screenheight() / 2 - 200)
        ))
        label = Label(self, text='Which folders would you like to organize?', font=font, bg=bg, fg=fg)
        label.pack(side=TOP, fill=X, ipady=20, ipadx=20)

        options_frame = Frame(self, bg=bg, bd=2, relief=SUNKEN)
        options_frame.pack(side=TOP, fill=BOTH, expand=True)

        for media_type, path in CONFIG.paths.to_dict().items():
            app.selected_media.add(path)
            b = CheckBox(
                options_frame, text=os.path.basename(path), font=CONFIG.fonts.xsmall,
                tooltip=path,
                expandable=False,
                metadata={'path': path},
                on_toggle_on=lambda x: self.on_add(x, app),
                on_toggle_off=lambda x: self.on_remove(x, app)
            )
            b.pack(side=TOP, fill=X, anchor=NW, padx=(10, 0))
        submit_button = OMButton(
            self, text='Select', command=lambda x=app: self.on_submit(x), font=CONFIG.fonts.small,
            highlight_bg=CONFIG.colors.special
        )
        submit_button.pack(side=BOTTOM, pady=20)

    @staticmethod
    def on_add(metadata, app):
        app.selected_media.add(metadata['path'])

    @staticmethod
    def on_remove(metadata, app):
        app.selected_media.remove(metadata['path'])

    @staticmethod
    def on_submit(app):
        app.change_screen('main')
