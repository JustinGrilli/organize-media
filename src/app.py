import os
import yaml
from tkinter import *

from screens import FreshStartup, Main
from components.data import CONFIG, user_settings_template, Images, OMImage
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
        self.mouse_edges = set()
        self.config(bg=CONFIG.colors.main)
        self.geometry(CONFIG.geometry)
        self.title(CONFIG.title)
        self.__images = Images()
        # self.iconbitmap('Images/toolbar_icon.ico')
        # self.iconphoto(True, self.__images.organize)
        self.titlebar = TitleBar(self, image=self.__images.icon)
        self.titlebar.pack(side=TOP, fill=X)
        self.settings = self.__get_user_settings()
        # Screen
        dl_path = self.settings['paths'].get('downloads')
        media_path = self.settings['paths'].get('media')
        if not dl_path or not media_path:
            self.screen = FreshStartup(self)
        else:
            self.screen = Main(self)
        self.screen.pack(fill=BOTH, expand=True)
        self.bind('<Button-1>', self.adjust_window)
        self.bind('<Motion>', self.mouse_position)

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

    def mouse_position(self, event):
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

    def adjust_window(self, event):
        """ Adjusts the geometry of the window, based on the edge(s) the mouse cursor is near """
        if not self.mouse_edges:
            return None

        w, h, x, y = self.winfo_width(), self.winfo_height(), self.winfo_x(), self.winfo_y()
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
        print('Changed Screens')
        self.screen.pack_forget()
        self.screen.destroy()
        self.screen = SCREENS[next_screen](self)
        self.screen.pack(fill=BOTH, expand=True)


app = OrganizeMedia()
app.mainloop()
