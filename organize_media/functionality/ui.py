from tkinter import *
from .data import Images, CONFIG
from dataclasses import dataclass


class OMButton(Frame):
    """ A button that contains an image, a label below the image, and a tooltip. """

    def __init__(self, master, image, text, tooltip, command=None,
                 font=CONFIG.fonts.xsmall,
                 bg=CONFIG.colors.main,
                 fg=CONFIG.colors.font,
                 *args, **kwargs):
        """
        Args:
            image (Any):
            text (str):
            font (tuple):
            tooltip (str):
            command (Any):
            bg (str):
            fg (str):
        """
        Frame.__init__(self, master, bg=bg, *args, **kwargs)
        self.command = command
        self.image = image
        self.tooltip = tooltip
        self.bg = bg
        self.fg = fg
        self.button = Button(self, image=self.image, command=self.command,
                             bg=self.bg, cursor="hand2", relief=FLAT, anchor=CENTER)
        self.label = Label(self, text=text, font=font, bg=bg, fg=fg)

        # Tooltip
        self.tooltip_id = None
        self.tooltip_widget = None

        self.button.bind('<Enter>', self.__mouse_enter)
        self.button.bind('<Leave>', self.__mouse_leave)

    def __mouse_enter(self, event):
        if self.button['state'] != DISABLED:
            self.button.config(bg=CONFIG.colors.sub)
            self.__schedule_tooltip()

    def __mouse_leave(self, event):
        self.button.config(bg=CONFIG.colors.main)
        self.__unschedule_tooltip()
        self.__hide_tooltip()

    def __show_tooltip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.bbox("insert")
        x += self.winfo_pointerx() + 10
        y += self.winfo_pointery() + 10
        # creates a toplevel window
        self.tooltip_widget = Toplevel(self)
        # Leaves only the label and removes the app window
        self.tooltip_widget.wm_overrideredirect(True)
        self.tooltip_widget.wm_geometry(f"+{x}+{y}")
        label = Label(self.tooltip_widget, text=self.tooltip, justify='left',
                      background=self.bg, foreground=self.fg, relief='solid', borderwidth=1,
                      wraplength=180)
        label.pack(ipadx=1)

    def __hide_tooltip(self):
        tw = self.tooltip_widget
        self.tooltip_widget = None
        if tw:
            tw.destroy()

    def __schedule_tooltip(self):
        if not self.tooltip:
            return None
        self.__unschedule_tooltip()
        self.tooltip_id = self.after(500, self.__show_tooltip)

    def __unschedule_tooltip(self):
        tooltip_id = self.tooltip_id
        self.tooltip_id = None
        if tooltip_id:
            self.after_cancel(tooltip_id)

    def enable(self):
        self.button.config(state=NORMAL)

    def disable(self):
        self.button.config(state=DISABLED, bg=CONFIG.colors.main)
        self.__unschedule_tooltip()
        self.__hide_tooltip()

    def update(self):
        self.button.update()
        self.label.update()
        super().update()

    def pack(self, *args, **kwargs):
        self.button.pack(fill=X)
        self.label.pack(fill=X)
        super().pack(*args, **kwargs)


@dataclass
class Buttons:
    master: [Widget]
    locate_media: [OMButton] = None
    select_media: [OMButton] = None
    organize: [OMButton] = None

    def __list_buttons(self):
        return [
            self.locate_media,
            self.select_media,
            self.organize,
        ]

    def init(self):
        self.locate_media = OMButton(
            master=self.master,
            image=Images.locate_media.get(),
            text='Locate Media',
            tooltip='Select your downloads folder and media folder; Your media folder will contain'
                    ' your "Movies" and "TV Shows" folders'
        )
        self.select_media = OMButton(
            master=self.master,
            image=Images.select_media.get(),
            text='Select Media',
            tooltip='Gathers a list of media files from your downloads folder, and'
                    ' allows you to filter which files to organize'
        )
        self.organize = OMButton(
            master=self.master,
            image=Images.organize.get(),
            text='Organize',
            tooltip='Organize your media into Movies/TV Shows folders:\n\n'
                    'If you have a Movies/TV Shows folder with a name other than "Movies" or "TV Shows",'
                    ' in your media folder, you should rename them. Casing matters!\n\n'
                    'If you do not have the folders, they will be created for you.'
        )

    def enable(self):
        for button in self.__list_buttons():
            button.enable()

    def disable(self):
        for button in self.__list_buttons():
            button.disable()

    def update(self):
        for button in self.__list_buttons():
            button.update()

    def pack(self, *args, **kwargs):
        for button in self.__list_buttons():
            button.pack(*args, **kwargs)
