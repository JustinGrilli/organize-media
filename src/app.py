from tkinter import Tk, Toplevel, TOP, X, BOTH

from screens import FreshStartup, Main, SelectMedia
from components.data import CONFIG, Images
from components import TitleBar


SCREENS = {
    'fresh_startup': FreshStartup,
    'main': Main,
    'select_media': SelectMedia,
}


class MainWindow(Toplevel):
    def __init__(self, app, *args, **kwargs):
        """
        Args:
            app (Tk):
        """
        Toplevel.__init__(self, app, *args, **kwargs)
        self.geometry(CONFIG.geometry)
        self.overrideredirect(True)
        self.is_fullscreen = False
        self.mouse_edges = set()

        self.selected_media = set()

        self.__images = Images()
        self.titlebar = TitleBar(self, image=self.__images.icon)
        self.titlebar.pack(side=TOP, fill=X)

        # Screen
        dl_path = CONFIG.paths.downloads
        media_path = CONFIG.paths.media
        if not dl_path or not media_path:
            self.screen = FreshStartup(self)
        else:
            self.screen = Main(self)
        self.screen.pack(fill=BOTH, expand=True)

        self.bind('<Button-1>', self.__adjust_window)
        self.bind('<Motion>', self.__mouse_position)

    def __mouse_position(self, event):
        """
            Changes the mouse cursor if it is near an edge/corner of the window,
            and detects which edge(s) the cursor is near.
        """
        # Side is within <buffer> pixels
        buffer = 7
        left = 0 < event.x_root - self.winfo_x() <= buffer
        right = 0 < (self.winfo_x() + self.winfo_width()) - event.x_root <= buffer
        top = 0 < event.y_root - self.winfo_y() <= buffer
        bottom = 0 < (self.winfo_y() + self.winfo_height()) - event.y_root <= buffer
        if left and top:
            self.mouse_edges.add('left')
            self.mouse_edges.add('top')
            self.config(cursor='top_left_corner')
        elif left and bottom:
            self.mouse_edges.add('left')
            self.mouse_edges.add('bottom')
            self.config(cursor='bottom_left_corner')
        elif right and top:
            self.mouse_edges.add('right')
            self.mouse_edges.add('top')
            self.config(cursor='top_right_corner')
        elif right and bottom:
            self.mouse_edges.add('right')
            self.mouse_edges.add('bottom')
            self.config(cursor='bottom_right_corner')
        elif left:
            self.mouse_edges.add('left')
            self.config(cursor='sb_h_double_arrow')
        elif right:
            self.mouse_edges.add('right')
            self.config(cursor='sb_h_double_arrow')
        elif top:
            self.mouse_edges.add('top')
            self.config(cursor='sb_v_double_arrow')
        elif bottom:
            self.mouse_edges.add('bottom')
            self.config(cursor='sb_v_double_arrow')
        elif self.mouse_edges:
            self.mouse_edges = set()
            self.config(cursor='arrow')

    def __adjust_window(self, event):
        """ Adjusts the geometry of the window, based on the edge(s) the mouse cursor is near """
        if not self.mouse_edges:
            return None

        w, h = self.winfo_width(), self.winfo_height()
        x, y = self.winfo_x(), self.winfo_y()
        click_start_x = event.x_root
        click_start_y = event.y_root

        def on_drag(e):
            mouse_x_diff = click_start_x - e.x_root
            mouse_y_diff = click_start_y - e.y_root
            if 'left' in self.mouse_edges and 'bottom' in self.mouse_edges:
                self.geometry(f'{w + mouse_x_diff}x{h - mouse_y_diff}+{e.x_root}+{y}')
            elif 'left' in self.mouse_edges and 'top' in self.mouse_edges:
                self.geometry(f'{w + mouse_x_diff}x{h + mouse_y_diff}+{e.x_root}+{e.y_root}')
            elif 'right' in self.mouse_edges and 'top' in self.mouse_edges:
                self.geometry(f'{w - mouse_x_diff}x{h + mouse_y_diff}+{x}+{e.y_root}')
            elif 'right' in self.mouse_edges and 'bottom' in self.mouse_edges:
                self.geometry(f'{w - mouse_x_diff}x{h - mouse_y_diff}+{x}+{y}')
            elif 'right' in self.mouse_edges:
                self.geometry(f'{w - mouse_x_diff}x{h}+{x}+{y}')
            elif 'top' in self.mouse_edges:
                self.geometry(f'{w}x{h + mouse_y_diff}+{x}+{e.y_root}')
            elif 'left' in self.mouse_edges:
                self.geometry(f'{w + mouse_x_diff}x{h}+{e.x_root}+{y}')
            elif 'bottom' in self.mouse_edges:
                self.geometry(f'{w}x{h - mouse_y_diff}+{x}+{y}')

        self.bind('<B1-Motion>', on_drag)

    def change_screen(self, next_screen):
        """
        Args:
            next_screen (str):
        """
        self.screen.pack_forget()
        self.screen.destroy()
        self.screen = SCREENS[next_screen](self)
        self.screen.pack(fill=BOTH, expand=True)

    def minimize(self):
        self.master.iconify()

    def maximize(self):
        self.wm_attributes('-alpha', 0)
        self.overrideredirect(False)
        if self.is_fullscreen:
            self.wm_attributes('-fullscreen', 0)
            self.is_fullscreen = False
        else:
            self.wm_attributes('-fullscreen', 1)
            self.is_fullscreen = True
        self.wm_attributes('-alpha', 1)
        self.overrideredirect(True)

    def destroy(self):
        super().destroy()
        self.master.destroy()


class OrganizeMedia(Tk):
    """ Utility GUI Tool, used to rename and organize media files -
        such as Movies and TV Shows - into appropriate folders. """

    def __init__(self):
        Tk.__init__(self)
        self.wm_attributes('-alpha', 0)
        self.config(bg=CONFIG.colors.main)
        self.title(CONFIG.title)
        self.iconbitmap('Images/toolbar_icon.ico')
        self.window = MainWindow(self, bg=CONFIG.colors.main)

        self.bind('<Unmap>', self.__on_unmap)
        self.bind('<Map>', self.__on_map)
        # Defer the focus to the main window
        self.bind('<FocusIn>', self.__on_focus)

    def __on_focus(self, event):
        """ Defer the focus to the MainWindow """
        self.window.focus()

    def __on_unmap(self, event):
        self.window.withdraw()

    def __on_map(self, event):
        self.window.deiconify()


app = OrganizeMedia()
app.mainloop()
