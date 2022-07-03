from tkinter import *
from .data import Images, CONFIG


class ScrollFrame(Frame):
    def __init__(self, widget, bd=0, relief=None, bg=CONFIG.colors.main, *arg, **kwargs):
        self.canvas = Canvas(widget, bg=bg, bd=bd, relief=relief, highlightthickness=0, *arg, **kwargs)
        Frame.__init__(self, self.canvas, bg=bg)
        self.name = 'ScrollFrame'

        # Scrollbars
        ybar = Scrollbar(widget, command=self.canvas.yview, orient=VERTICAL)
        xbar = Scrollbar(widget, command=self.canvas.xview, orient=HORIZONTAL)

        self.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all"),
            width=self.winfo_width(),
            height=self.winfo_height()
        ))
        self.canvas.create_window((0, 0), window=self, anchor=NW)
        self.canvas.config(yscrollcommand=ybar.set, xscrollcommand=xbar.set)

        ybar.pack(side=RIGHT, fill=Y)
        xbar.pack(side=BOTTOM, fill=X)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.bind_all("<MouseWheel>", self.__on_mousewheel)

    def __get_scroll_frame_from_parents(self, widget):
        """
        Args:
            widget (Widget):
        """
        if not widget:
            return widget

        if widget.__dict__.get('name') == 'ScrollFrame':
            return widget

        return self.__get_scroll_frame_from_parents(widget.master)

    def __get_scroll_frame_from_children(self, widget):
        """
        Args:
            widget (Widget):
        """
        if not widget:
            return widget

        for child in widget.winfo_children():
            if child.__dict__.get('name') == 'ScrollFrame':
                return child
            return self.__get_scroll_frame_from_children(child)

    def __on_mousewheel(self, event):
        x, y = self.winfo_pointerxy()
        target = self.winfo_containing(x, y)

        if target.__dict__.get('name') == 'ScrollFrame':
            scroll_frame = target
        else:
            scroll_frame = self.__get_scroll_frame_from_parents(target)
        if not scroll_frame:
            scroll_frame = self.__get_scroll_frame_from_children(target)

        if scroll_frame:
            scroll_frame.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def pack(self, *args, **kwargs):
        # super().pack(*args, **kwargs)
        pass


class OMLabel(Label):
    def __init__(self, widget,
                 bg=CONFIG.colors.main,
                 highlight_bg=CONFIG.colors.sub,
                 fg=CONFIG.colors.font,
                 tooltip=None, *args, **kwargs):
        Label.__init__(self, widget, bg=bg, fg=fg, *args, **kwargs)
        # Tooltip
        self.default_bg = bg
        self.highlight_bg = highlight_bg
        self.tooltip = tooltip
        self.tooltip_id = None
        self.tooltip_widget = None

        self.bind('<Enter>', self.__mouse_enter)
        self.bind('<Leave>', self.__mouse_leave)

    def config(self, *args, **kwargs):
        """
        Args:

        Keyword Args:
            highlight_bg (str): The highlighting color on mouse hover
            default_bg (str): The default background color
            bg (str): The current background color
        """
        if 'highlight_bg' in kwargs:
            self.highlight_bg = kwargs.pop('highlight_bg')
        if 'default_bg' in kwargs:
            self.default_bg = kwargs.pop('default_bg')
        super().config(*args, **kwargs)

    def __mouse_enter(self, event):
        if self['state'] != DISABLED:
            self.config(bg=self.highlight_bg)
            self.__schedule_tooltip()

    def __mouse_leave(self, event):
        self.config(bg=self.default_bg)
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
                      background=self['bg'], foreground=self['fg'], relief='solid', borderwidth=1,
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


class OMButton(Button):
    def __init__(self, widget,
                 cursor="hand2",
                 fg=CONFIG.colors.font,
                 bg=CONFIG.colors.main,
                 highlight_bg=CONFIG.colors.sub,
                 tooltip=None, *args, **kwargs):
        Button.__init__(self, widget, cursor=cursor, bg=bg, fg=fg,
                        activebackground=highlight_bg,
                        activeforeground=fg,
                        *args, **kwargs)
        # Tooltip
        self.default_bg = bg
        self.highlight_bg = highlight_bg
        self.tooltip = tooltip
        self.tooltip_id = None
        self.tooltip_widget = None

        self.bind('<Enter>', self.__mouse_enter)
        self.bind('<Leave>', self.__mouse_leave)

    def config(self, *args, **kwargs):
        """
        Args:

        Keyword Args:
            highlight_bg (str): The highlighting color on mouse hover
            default_bg (str): The default background color
            bg (str): The current background color
        """
        if 'highlight_bg' in kwargs:
            self.highlight_bg = kwargs.pop('highlight_bg')
        if 'default_bg' in kwargs:
            self.default_bg = kwargs.pop('default_bg')
        super().config(*args, **kwargs)

    def __mouse_enter(self, event):
        if self['state'] != DISABLED:
            self.config(bg=self.highlight_bg)
            self.__schedule_tooltip()

    def __mouse_leave(self, event):
        self.config(bg=self.default_bg)
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
                      background=self['bg'], foreground=self['fg'], relief='solid', borderwidth=1,
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

    def config(self, *args, **kwargs):
        # Label specific
        if 'text' in kwargs:
            self.label.config(text=kwargs.pop('text'))
        if 'font' in kwargs:
            self.label.config(font=kwargs.pop('font'))
        if 'fg' in kwargs:
            self.label.config(fg=kwargs.pop('fg'))
        # Button specific
        if 'command' in kwargs:
            self.button.config(command=kwargs.pop('command'))
        if 'relief' in kwargs:
            self.button.config(relief=kwargs.pop('relief'))
        if 'bd' in kwargs:
            self.button.config(bd=kwargs.pop('bd'))
        # Applies to all (e.g. bg)
        self.button.config(*args, **kwargs)
        self.label.config(*args, **kwargs)
        super().config(*args, **kwargs)

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

    def __init__(self):
        self.__images = Images()

    def locate_media(self, widget):
        """
        Args:
            widget (Widget): The widget that this button will be packed into

        Returns: The locate_media button
        """
        return TextImageButton(
            widget=widget,
            image=self.__images.locate_media,
            text='Locate Media',
            tooltip='Select your downloads folder and media folder; Your media folder will contain'
                    ' your "Movies" and "TV Shows" folders'
        )

    def select_media(self, widget):
        """
        Args:
            widget (Widget): The widget that this button will be packed into

        Returns: The select_media button
        """
        return TextImageButton(
            widget=widget,
            image=self.__images.select_media,
            text='Select Media',
            tooltip='Gathers a list of media files from your downloads folder, and'
                    ' allows you to filter which files to organize'
        )

    def organize(self, widget):
        """
        Args:
            widget (Widget): The widget that this button will be packed into

        Returns: The organize button
        """
        return TextImageButton(
            widget=widget,
            image=self.__images.organize,
            text='Organize',
            tooltip='Organize your media into Movies/TV Shows folders:\n\n'
                    'If you have a Movies/TV Shows folder with a name other than "Movies" or "TV Shows",'
                    ' in your media folder, you should rename them. Casing matters!\n\n'
                    'If you do not have the folders, they will be created for you.'
        )


class ButtonGroup:

    def __init__(self, widget):
        """
        Args:
            widget (Widget):
        """
        self.__images = Images()
        self.__buttons = Buttons()

        self.locate_media = self.__buttons.locate_media(widget)
        self.select_media = self.__buttons.select_media(widget)
        self.organize = self.__buttons.organize(widget)

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
                 tooltip=None,
                 metadata: dict = None,
                 expandable: bool = True,
                 on_toggle_off=None,
                 on_toggle_on=None,
                 *args, **kwargs):
        Frame.__init__(self, widget, bd=0, bg=bg, *args, **kwargs)
        self.header_bg = header_bg
        self.title_bg = title_bg
        self.bg = bg
        self.selected_bg = selected_bg
        self.fg = fg
        self.font = font
        self.selected = True
        self.metadata = metadata
        self.expandable = expandable
        self.name = 'CheckBox'

        # User defined functions for toggling off/on.
        # These functions are expected to accept the metadata provided.
        self.on_toggle_off = on_toggle_off
        self.on_toggle_on = on_toggle_on

        self.__images = Images()

        self.header_frame = Frame(self, bg=self.header_bg, bd=0)
        self.button = OMButton(self.header_frame, image=self.__images.deselect, cursor='hand2', bg=self.bg,
                               command=self.toggle_checkbox, relief=FLAT, anchor=W)
        title_attributes = {
            'text': text,
            'font': self.font,
            'tooltip': tooltip,
            'bg': self.selected_bg,
            'highlight_bg': self.selected_bg,
            'fg': self.fg,
            'relief': RAISED,
            'anchor': W,
            'justify': LEFT
        }
        if self.expandable:
            self.content_frame = Frame(self, bg=self.bg, bd=0)
            self.title = OMButton(self.header_frame, cursor='hand2', command=self.__toggle_content, **title_attributes)
        else:
            self.title = OMLabel(self.header_frame, **title_attributes)

    def __toggle_content(self):
        """ Toggle the visibility of the content_frame """
        if self.content_frame.winfo_viewable():
            self.content_frame.pack_forget()
        else:
            self.content_frame.pack(side=TOP, fill=X, anchor=NW, padx=(30, 0))

    def toggle_checkbox(self):
        def upon_select(widget):
            """
            Args:
                widget (Widget|CheckBox):
            """
            if self.selected:
                widget.button.config(image=self.__images.select)
                widget.title.config(bg=widget.title_bg, default_bg=widget.title_bg)
                widget.title.config()
                widget.selected = False
                if widget.on_toggle_off:
                    widget.on_toggle_off(widget.metadata)
            else:
                widget.button.config(image=self.__images.deselect)
                widget.title.config(bg=widget.selected_bg, default_bg=widget.selected_bg)
                widget.selected = True
                if widget.on_toggle_on:
                    widget.on_toggle_on(widget.metadata)

        def toggle_children(widget):
            """
            Args:
                widget (Widget|CheckBox):
            """
            if 'content_frame' in list(widget.__dict__.keys()):
                children = [c for c in widget.content_frame.winfo_children()
                            if c.__dict__.get('name') == 'CheckBox']
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
        # The first level of the dictionary is considered the header
        for top_level_key, next_dict in items_dict.items():
            container = Frame(self, bg=self.bg)
            container.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)
            frame = ScrollFrame(container, bg=self.bg)
            title = Label(frame, text=top_level_key, bg=self.bg, fg=self.fg, font=self.font, anchor=NW, justify=LEFT)
            title.pack(side=TOP, fill=X, anchor=W)
            self.generate_checkboxes(frame, next_dict)

    def generate_checkboxes(self, widget, dictionary):
        """ Recursively generates nested checkboxes from the provided dictionary """
        for k, v in dictionary.items():
            checkbox = CheckBox(widget, text=k, font=CONFIG.fonts.small)
            checkbox.pack(side=TOP, fill=X, anchor=NW)
            if isinstance(v, dict):
                self.generate_checkboxes(checkbox.content_frame, v)
            elif isinstance(v, list):
                for item in v:
                    on_toggle_off = item.pop('on_toggle_off', None)
                    on_toggle_on = item.pop('on_toggle_on', None)
                    metadata = item if on_toggle_off and on_toggle_on else None
                    content_checkbox = CheckBox(
                        checkbox.content_frame,
                        text=item.get('renamed_file_name'),
                        font=CONFIG.fonts.xsmall,
                        tooltip=item.get('file_path'),
                        expandable=False,
                        on_toggle_off=on_toggle_off,
                        on_toggle_on=on_toggle_on,
                        metadata=metadata
                    )
                    content_checkbox.pack(side=TOP, fill=X, anchor=NW)
