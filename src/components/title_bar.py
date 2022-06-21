from tkinter import *
from .data import CONFIG, Images


class TitleBar(Frame):
    def __init__(self, app,
                 bg=CONFIG.colors.sub,
                 fg=CONFIG.colors.font,
                 font=CONFIG.fonts.xsmall,
                 bd=1,
                 relief=RIDGE,
                 *args, **kwargs):
        Frame.__init__(self, app, bg=bg, bd=bd, relief=relief, *args, **kwargs)
        images = Images()
        icon_img = images.organize
        icon_img.resize(24, 24)
        icon = Label(self, image=icon_img, bg=bg)
        icon.pack(side=LEFT)
        self.title = Label(self, text=CONFIG.title, bg=bg, fg=fg, font=font)
        self.title.pack(side=LEFT, fill=X, expand=True)
        close_button = Button(self, text='X', command=app.destroy, width=2, height=1, bd=1, relief=RIDGE,
                              bg=CONFIG.colors.special, fg=fg, font=font)
        close_button.pack(side=RIGHT, anchor=NE)
        min_button = Button(self, text='-', command=app.minimize, width=2, height=1, bd=1, relief=RIDGE,
                            bg=CONFIG.colors.special_alt, fg=fg, font=font)
        min_button.pack(side=RIGHT, anchor=NE)
        self.title.bind('<Button-1>', self.on_click)

    def on_click(self, event):
        x_diff = self.master.winfo_x() - event.x_root
        y_diff = self.master.winfo_y() - event.y_root

        def on_drag(e):
            self.master.geometry(f'+{e.x_root + x_diff}+{e.y_root + y_diff}')

        self.title.bind('<B1-Motion>', on_drag)
