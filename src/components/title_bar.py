"""
...... Inactive ......
Functionality needed:
    - Adjust window size
    - Toolbar icon when showing
"""
from tkinter import *
from .data import CONFIG, Images
from .ui import OMButton


class TitleBar(Frame):
    def __init__(self, app,
                 bg=CONFIG.colors.sub,
                 fg=CONFIG.colors.font,
                 font=CONFIG.fonts.small,
                 image=None,
                 bd=1,
                 relief=RIDGE,
                 *args, **kwargs):
        Frame.__init__(self, app, bg=bg, bd=bd, relief=relief, *args, **kwargs)
        icon = Label(self, image=image, bg=bg)
        icon.pack(side=LEFT)
        self.__is_fullscreen = False
        self.title = Label(self, text=CONFIG.title, bg=bg, fg=fg, font=font)
        self.title.pack(side=LEFT, fill=X, expand=True)
        button_attribs = {
            'width': 3, 'height': 1, 'bd': 0, 'font': font,
            'bg': bg, 'fg': fg
        }
        min_button = OMButton(self, text='-', command=lambda x=app: self.__minimize(x),
                              highlight_bg=CONFIG.colors.alt, **button_attribs)
        max_button = OMButton(self, text='^', command=lambda x=app: self.__maximize(x),
                              highlight_bg=CONFIG.colors.alt, **button_attribs)
        close_button = OMButton(self, text='X', command=app.destroy,
                                highlight_bg=CONFIG.colors.special_alt,  **button_attribs)
        close_button.pack(side=RIGHT, anchor=NE)
        max_button.pack(side=RIGHT, anchor=NE)
        min_button.pack(side=RIGHT, anchor=NE)
        self.title.bind('<Button-1>', lambda x: self.on_click(x, app))
        app.bind('<Map>', lambda x: self.__on_map(x, app))

    @staticmethod
    def __on_map(event, app):
        app.state('normal')
        app.overrideredirect(True)

    @staticmethod
    def __minimize(app):
        app.state('withdrawn')
        app.overrideredirect(False)
        app.iconify()

    def __maximize(self, app):
        app.wm_attributes('-alpha', 0)
        app.overrideredirect(False)
        if self.__is_fullscreen:
            app.wm_attributes('-fullscreen', 0)
            self.__is_fullscreen = False
        else:
            app.wm_attributes('-fullscreen', 1)
            self.__is_fullscreen = True
        app.wm_attributes('-alpha', 1)
        app.overrideredirect(True)

    def on_click(self, event, app):
        x_diff = app.winfo_x() - event.x_root
        y_diff = app.winfo_y() - event.y_root
        from_fullscreen = self.__is_fullscreen

        def on_drag(e):
            if self.__is_fullscreen:
                app.overrideredirect(False)
                app.wm_attributes('-alpha', 0)
                app.wm_attributes('-fullscreen', 0)
                self.__is_fullscreen = False
                app.wm_attributes('-alpha', 1)
                app.overrideredirect(True)
            elif from_fullscreen:
                app.geometry(f'+{e.x_root - round(self.winfo_width() / 2)}+{e.y_root - 20}')
            else:
                app.geometry(f'+{e.x_root + x_diff}+{e.y_root + y_diff}')

        self.title.bind('<B1-Motion>', on_drag)
