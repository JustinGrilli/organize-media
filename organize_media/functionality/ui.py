from tkinter import *
from .data import Images, CONFIG


class OMButton(Button):
    def __init__(self, widget, tooltip=None, *args, **kwargs):
        Button.__init__(self, widget, *args, **kwargs)
        # Tooltip
        self.bg = kwargs.get('bg', CONFIG.colors.main)
        self.fg = kwargs.get('fg', CONFIG.colors.font)
        self.tooltip = tooltip
        self.tooltip_id = None
        self.tooltip_widget = None

        self.bind('<Enter>', self.__mouse_enter)
        self.bind('<Leave>', self.__mouse_leave)

    def __mouse_enter(self, event):
        if self['state'] != DISABLED:
            self.config(bg=CONFIG.colors.sub)
            self.__schedule_tooltip()

    def __mouse_leave(self, event):
        self.config(bg=CONFIG.colors.main)
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


class TextImageButton(Frame):
    """ A button that contains an image, a label below the image, and a tooltip. """

    def __init__(self, widget, image, text, tooltip=None, bg=CONFIG.colors.main, fg=CONFIG.colors.font,
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
        Frame.__init__(self, widget, bg=bg, *args, **kwargs)
        self.image = image
        self.text = text
        self.tooltip = tooltip
        self.bg = bg
        self.fg = fg
        self.command = kwargs.pop('command', None)
        self.font = kwargs.pop('font', CONFIG.fonts.xsmall)
        self.button = OMButton(self, image=self.image, tooltip=self.tooltip, command=self.command,
                               bg=self.bg, cursor="hand2", relief=FLAT, anchor=CENTER)
        self.label = Label(self, text=self.text, font=self.font, bg=bg, fg=fg)

    def enable(self):
        self.button.config(state=NORMAL)

    def disable(self):
        self.button.config(state=DISABLED, bg=CONFIG.colors.main)

    def update(self):
        self.button.update()
        self.label.update()
        super().update()

    def pack(self, *args, **kwargs):
        self.button.pack(fill=X)
        self.label.pack(fill=X)
        super().pack(*args, **kwargs)


class Buttons:

    def __init__(self, widget):
        """
        Args:
            widget (Widget):
        """
        self.__images = Images()
        self.__images.populate()

        self.locate_media = TextImageButton(
            widget=widget,
            image=self.__images.locate_media,
            text='Locate Media',
            tooltip='Select your downloads folder and media folder; Your media folder will contain'
                    ' your "Movies" and "TV Shows" folders'
        )
        self.select_media = TextImageButton(
            widget=widget,
            image=self.__images.select_media,
            text='Select Media',
            tooltip='Gathers a list of media files from your downloads folder, and'
                    ' allows you to filter which files to organize'
        )
        self.organize = TextImageButton(
            widget=widget,
            image=self.__images.organize,
            text='Organize',
            tooltip='Organize your media into Movies/TV Shows folders:\n\n'
                    'If you have a Movies/TV Shows folder with a name other than "Movies" or "TV Shows",'
                    ' in your media folder, you should rename them. Casing matters!\n\n'
                    'If you do not have the folders, they will be created for you.'
        )

    def __list_buttons(self):
        return [
            self.locate_media,
            self.select_media,
            self.organize,
        ]

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


class CheckBox(Frame):

    def __init__(self, widget, text,
                 header_bg=CONFIG.colors.special,
                 title_bg=CONFIG.colors.main,
                 bg=CONFIG.colors.main,
                 selected_bg=CONFIG.colors.sub,
                 fg=CONFIG.colors.font,
                 font=CONFIG.fonts.medium,
                 metadata=None,
                 expandable=True,
                 *args, **kwargs):
        Frame.__init__(self, widget, bd=0, bg=bg, *args, **kwargs)
        self.header_bg = header_bg
        self.title_bg = title_bg
        self.bg = bg
        self.selected_bg = selected_bg
        self.fg = fg
        self.font = font
        self.selected = False
        self.metadata = metadata
        self.expandable = expandable
        self.name = 'CheckBox'

        self.__images = Images()
        self.__images.populate()

        self.header_frame = Frame(self, bg=self.header_bg, bd=0)
        self.button = OMButton(self.header_frame, image=self.__images.deselect, cursor='hand2', bg=self.bg,
                             command=self.toggle_checkbox, relief=FLAT, anchor=W)
        if self.expandable:
            self.content_frame = Frame(self, bg=self.bg, bd=0)
            self.title = OMButton(self.header_frame, text=text, cursor='hand2', bg=self.title_bg, fg=self.fg, font=self.font,
                                command=self.__toggle_content, relief=RAISED, anchor=W, justify=LEFT)
        else:
            self.title = Label(self.header_frame, text=text, bg=self.title_bg, fg=self.fg, font=self.font,
                               relief=RAISED, anchor=W, justify=LEFT)

    def __toggle_content(self):
        """ Toggle the visibility of the content_frame """
        if self.content_frame.winfo_viewable():
            self.content_frame.pack_forget()
        else:
            self.content_frame.pack(side=TOP, fill=X, anchor=NW, padx=(30, 0))

    def toggle_checkbox(self):
        def upon_select(widget):
            if self.selected:
                widget.button.config(image=self.__images.deselect)
                widget.title.config(bg=self.title_bg)
                widget.selected = False
            else:
                widget.button.config(image=self.__images.select)
                widget.title.config(bg=self.selected_bg)
                widget.selected = True

        def toggle_children(widget):
            if 'content_frame' in list(widget.__dict__.keys()):
                children = [c for c in widget.content_frame.winfo_children()
                            if c.name == 'CheckBox']
                for c in children:
                    upon_select(c)
                    toggle_children(c)

        toggle_children(self)
        upon_select(self)

    def pack(self, *args, **kwargs):
        self.header_frame.pack(side=TOP, fill=X, anchor=NW)
        if self.expandable:
            self.content_frame.pack(side=TOP, fill=X, anchor=NW, padx=(30, 0))
        self.button.pack(side=LEFT, fill=Y, anchor=W)
        self.title.pack(side=LEFT, fill=BOTH, expand=True, anchor=W, padx=1, pady=1)
        super().pack(*args, **kwargs)


class CheckBoxes(Frame):

    def __init__(self, widget, items_dict,
                 bg=CONFIG.colors.main,
                 fg=CONFIG.colors.font,
                 font=CONFIG.fonts.large,
                 *args, **kwargs):
        Frame.__init__(self, widget, bg=bg, bd=0, *args, **kwargs)
        self.bg = bg
        self.fg = fg
        self.font = font
        for top_level_key, next_dict in items_dict.items():
            frame = Frame(self, bg=self.bg, bd=0, relief=RIDGE)
            frame.pack(side=LEFT, padx=4, pady=4, anchor=N)
            title = Label(frame, text=top_level_key, bg=self.bg, fg=self.fg, font=self.font, anchor=NW, justify=LEFT)
            title.pack(side=TOP, fill=X, anchor=W)
            self.generate_checkboxes(frame, next_dict)

    def generate_checkboxes(self, widget, dictionary):
        for k, v in dictionary.items():
            checkbox = CheckBox(widget, text=k, font=CONFIG.fonts.small)
            checkbox.pack(side=TOP, fill=X, anchor=NW)
            if isinstance(v, dict):
                self.generate_checkboxes(checkbox.content_frame, v)
            elif isinstance(v, list):
                for item in v:
                    content_checkbox = CheckBox(
                        checkbox.content_frame, text=item['renamed_file_name'],
                        font=CONFIG.fonts.xsmall, expandable=False
                    )
                    content_checkbox.pack(side=TOP, fill=X, anchor=NW)
