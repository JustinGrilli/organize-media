from tkinter import *
from .data import CONFIG
from .ui import OMButton


class TitleBar(Frame):
    def __init__(self, window,
                 bg=CONFIG.colors.sub,
                 fg=CONFIG.colors.font,
                 font=CONFIG.fonts.small,
                 image=None,
                 bd=1,
                 relief=RIDGE,
                 *args, **kwargs):
        """
        Args:
            window (src.app.MainWindow):
        """
        Frame.__init__(self, window, bg=bg, bd=bd, relief=relief, *args, **kwargs)
        icon = Label(self, image=image, bg=bg)
        icon.pack(side=LEFT)
        self.title = Label(self, text=CONFIG.title, bg=bg, fg=fg, font=font)
        self.title.pack(side=LEFT, fill=X, expand=True)
        button_attribs = {
            'width': 3, 'height': 1, 'bd': 0, 'font': font,
            'bg': bg, 'fg': fg
        }
        min_button = OMButton(self, text='-', command=window.minimize,
                              highlight_bg=CONFIG.colors.alt, **button_attribs)
        max_button = OMButton(self, text='⛶', command=window.maximize,
                              highlight_bg=CONFIG.colors.alt, **button_attribs)
        close_button = OMButton(self, text='X', command=window.destroy,
                                highlight_bg=CONFIG.colors.special_alt, **button_attribs)
        close_button.pack(side=RIGHT, anchor=NE)
        max_button.pack(side=RIGHT, anchor=NE)
        min_button.pack(side=RIGHT, anchor=NE)
        self.title.bind('<Button-1>', lambda x: self.on_click(x, window))

    @staticmethod
    def __on_map(event, window):
        window.state('normal')
        window.overrideredirect(True)

    def on_click(self, event, window):
        x_diff = window.winfo_x() - event.x_root
        y_diff = window.winfo_y() - event.y_root
        from_fullscreen = window.is_fullscreen

        def on_drag(e):
            if window.is_fullscreen:
                window.overrideredirect(False)
                window.wm_attributes('-alpha', 0)
                window.wm_attributes('-fullscreen', 0)
                window.is_fullscreen = False
                window.wm_attributes('-alpha', 1)
                window.overrideredirect(True)
            elif from_fullscreen:
                window.geometry(f'+{e.x_root - round(self.winfo_width() / 2)}+{e.y_root - 20}')
            else:
                window.geometry(f'+{e.x_root + x_diff}+{e.y_root + y_diff}')

        self.title.bind('<B1-Motion>', on_drag)
