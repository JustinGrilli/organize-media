import threading
import shutil
import os
import json
from pathlib import Path
from tkinter import *
from tkinter.ttk import Progressbar, Style

from src.components.ui import ButtonGroup, CheckBoxes
from src.funcs.user_configuration import save_paths
from src.components.data import CONFIG, Images, MediaFile, MediaContainer

from pprint import pprint


class Main(Frame):
    def __init__(self, app, bg=CONFIG.colors.main, *args, **kwargs):
        """
        Args:
            app (Toplevel):
        """
        Frame.__init__(self, app, bg=bg, *args, **kwargs)
        app.geometry(CONFIG.geometry)
        # Used to cache info when exiting the application
        self.bind('<Destroy>', self.__on_destroy)
        # Images
        self.images = Images()

        ''' Filter media will contain a dictionary like:
                        {path: {file_name: name, title: title, kind: kind, ...}}'''
        self.media_containers: list[MediaContainer] = list()
        self.disable_buttons = False

        # Frames
        self.left_frame = Frame(self, bg=CONFIG.colors.main, bd=2, relief=RAISED)
        self.canvas_frame = Frame(self, bg=CONFIG.colors.main)
        self.status_bar = Canvas(self, bg=CONFIG.colors.sub, bd=0, highlightthickness=0,
                                 width=self.winfo_width(), height=0, relief=SUNKEN)
        self.status_bar.pack(side=BOTTOM, fill=X)
        self.left_frame.pack(side=LEFT, fill=Y, ipadx=14, ipady=14)
        self.canvas_frame.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)

        # Buttons
        self.buttons = ButtonGroup(self.left_frame)
        self.buttons.locate_media.config(command=self.locate_media)
        self.buttons.select_media.config(command=lambda x='select_media': app.change_screen(x))
        self.buttons.organize.config(command=self.on_press_organize_media)
        self.buttons.pack(side=TOP, padx=10, pady=10, fill=X)

        # Progress Bar
        self.s = Style()
        self.style = 'text.Horizontal.TProgressbar'
        self.s.theme_use('classic')
        # Add label in the layout
        self.s.layout(self.style,
                      [('Horizontal.Progressbar.trough',
                        {'children': [('Horizontal.Progressbar.pbar',
                                       {'side': 'left', 'sticky': 'ns'})],
                         'sticky': 'nsew'}),
                       ('Horizontal.Progressbar.label', {'sticky': ''})])
        # Set initial progress bar text
        self.s.configure(self.style, text='\n\n', troughcolor=CONFIG.colors.sub,
                         background=CONFIG.colors.special, foreground=CONFIG.colors.font,
                         font=CONFIG.fonts.xsmall, thickness=45)

        w = self.winfo_width()
        self.progress_bar = Progressbar(self.status_bar, style=self.style, length=w - 8)
        self.progress_bar.bind('<Configure>', self.on_progress_bar_adjust)
        # self.progress_bar.pack(side=BOTTOM)
        # self.status_bar.pack_forget()

        self.buttons.organize.pack_forget()
        if not CONFIG.paths.downloads:
            self.buttons.select_media.pack_forget()

        self.media_files_info(app.selected_media)

    def on_progress_bar_adjust(self, event):
        """ Handles resizing progress bar, when the app is resized """
        self.progress_bar.config(length=self.winfo_width()-8)

    def __on_destroy(self, event):
        """ Caches some information when the App is closed """
        cache = dict()
        cache['geometry'] = {
            'w': self.master.winfo_width(),
            'h': self.master.winfo_height(),
            'x': self.master.winfo_x(),
            'y': self.master.winfo_y(),
        }
        os.makedirs(os.path.dirname(CONFIG.cache_path), exist_ok=True)
        with open(CONFIG.cache_path, 'w') as file:
            json.dump(cache, file, indent=2)

    def get_media_info_from_paths(self, paths):
        """ Gets all media information from media files in the given paths

        Args:
            paths (list): A list of paths to media files

        Returns: A dictionary of information about each file
        """
        self.progress_bar_appear()
        self.progress_bar['maximum'] = len([
            file_name
            for path in paths
            for x, y, files in os.walk(path)
            for file_name in files
            if file_name.split('.')[-1] in CONFIG.media_extensions
        ])
        self.progress_bar['value'] = 0
        self.s.configure(style=self.style, text='Getting media info...')
        # Get a list of files to gather info for, and extract info from the local file
        for folder_path in paths:
            for path, folders, files in sorted(os.walk(folder_path)):
                for file in sorted(files):
                    current_file_path = os.path.join(path, file)
                    # Skip non-files
                    if not os.path.isfile(current_file_path):
                        continue
                    media_file = MediaFile(current_file_path, folder_path)
                    # Skip non-media files
                    if media_file.extension not in CONFIG.media_extensions:
                        continue
                    added = False
                    for c in self.media_containers:
                        if added:
                            continue
                        added = c.add_similar_media_file(media_file)
                    if not added:
                        mc = MediaContainer()
                        mc.add_similar_media_file(media_file)
                        self.media_containers.append(mc)
                    self.progress_bar['value'] += 1
                    self.s.configure(
                        style=self.style,
                        text=f'Got info for {file}\nIn the {folder_path} directory\n'
                    )
        self.progress_complete('Gathered Media!')

    def media_files_info(self, folder_paths):
        """ Gets information about each media file in a path, from IMDb.

        Output sample:
            'C:/USER/Downloads': {
                'C:/USER/Downloads/house.s01e01.avi': {
                    'title': 'House (2004)',
                    'title': 'House',
                    'renamed_file_name': 'House - S01E01 - Pilot',
                    'kind': 'TV Show',
                    'season': 1,
                    'episode': 1,
                    'genres': ['Drama', 'Comedy'],
                    'file_name': 'house.s01e01.avi'}}

        Args:
            folder_paths (list): The path to your media files

        Returns: A dictionary of information about each file
        """
        if not folder_paths:
            return None

        self.get_media_info_from_paths(folder_paths)

        if not self.media_containers:
            self.progress_bar_appear()
            self.progress_complete('\nNo Media Detected...\n')
            self.buttons.organize.pack_forget()
        else:
            self.filter_window()
            self.buttons.organize.pack(side=TOP, padx=10, pady=10, fill=X)

    def filter_window(self):
        """ The filter window that appears to filter the media files to be sorted. """

        def create_files_dict():
            """ Creates the media files dict, in a format that can be used to generate CheckBoxes.
                Here we also pass our on_toggle_off and on_toggle_on functions,
                as well as any additional metadata we need the CheckBox to have.

            Args:
                files (dict): The dict of all media files to be reformed

            Returns: The reformed files dict
            """
            new_files = dict()
            for container in self.media_containers:
                title = container.title
                kind = f'{container.type}s'
                for file in container.media_files:
                    # Reduce the display of the folder path to the last two folders, maximum
                    folder_path = Path(file.origin_dir).parts
                    if len(folder_path) > 1:
                        folder = os.path.join(*folder_path[-2:])
                    else:
                        folder = os.path.join(*folder_path)
                    metadata = dict()
                    metadata['origin_dir'] = file.origin_dir
                    metadata['file_path'] = file.path
                    metadata['file_rename'] = file.file_rename
                    metadata['on_toggle_off'] = file.deselect
                    metadata['on_toggle_on'] = file.select
                    new_files.setdefault(folder, {})
                    if kind == 'TV Shows':
                        season = f'Season {file.season}'
                        new_files[folder].setdefault(kind, {})
                        new_files[folder][kind].setdefault(title, {})
                        new_files[folder][kind][title].setdefault(season, [])
                        new_files[folder][kind][title][season].append(metadata)
                        # Sort the files by the new name
                        new_files[folder][kind][title][season] = list(sorted(
                            new_files[folder][kind][title][season], key=lambda f: f['file_rename']))
                    else:
                        new_files[folder].setdefault(kind, [])
                        new_files[folder][kind].append(metadata)
                        # Sort the files by the new name
                        new_files[folder][kind] = list(sorted(
                            new_files[folder][kind], key=lambda f: f['file_rename']))

            return new_files

        checkboxes = CheckBoxes(self.canvas_frame, create_files_dict())
        checkboxes.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)

    def recursively_organize_shows_and_movies(self, delete_folders=True):
        dl_path = CONFIG.paths.downloads
        media_path = CONFIG.paths.media
        folders_to_delete = []
        self.progress_bar_appear()
        self.progress_bar['maximum'] = len([
            m.path for c in self.media_containers
            for m in c.media_files if m.selected
        ])
        self.progress_bar['value'] = 0

        for container in self.media_containers:
            for media_file in container.media_files:
                if not media_file.selected:
                    continue
                # continue
                path = os.path.dirname(media_file.path)
                skip = False
                # Route for TV Shows
                if media_file.type == 'TV Show':
                    season_folder = f'Season {media_file.season}'
                    output_folder = os.path.join(media_path, 'TV Shows', container.title, season_folder)
                # Route for Movies
                else:
                    output_folder = os.path.join(media_path, 'Movies')
                output_path = os.path.join(output_folder, media_file.file_name)
                renamed_file_path = os.path.join(output_folder, media_file.file_rename)
                # Create output folder if it does not exist
                os.makedirs(output_folder, exist_ok=True)
                # Move and then rename file
                if not os.path.exists(output_path) and not os.path.exists(renamed_file_path):
                    shutil.move(media_file.path, output_path)
                    os.rename(output_path, renamed_file_path)
                    status_message = f'Moved & Renamed {media_file.type.title()}:\n' \
                                     f'From: {media_file.file_name}\n' \
                                     f'To: {media_file.file_rename}'
                    # Update status and increment progress bar to show that the file has moved
    
                elif not os.path.exists(renamed_file_path):
                    os.rename(output_path, renamed_file_path)
                    # Update status and increment progress bar to show that the file has moved
                    status_message = f'File exists in {output_folder}, Renamed {media_file.type.title()}:\n' \
                                     f'From: {media_file.file_name}\n' \
                                     f'To: {media_file.file_rename}'
                else:
                    skip = True
                    status_message = f'Skipping: {media_file.file_name}\n' \
                                     f'File exists in {output_folder}:\n' \
                                     f'{renamed_file_path}'
                self.progress_bar['value'] += 1
                self.s.configure(style=self.style, text=status_message)
                # Add the moved file's folder path to the list of folders to delete
                if path != dl_path and path != media_path and path != os.path.dirname(output_path) \
                        and path not in folders_to_delete and not skip:
                    folders_to_delete.append(path)

        # Delete folders that contained media files that were moved
        if delete_folders:
            for folder in folders_to_delete:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
        self.progress_complete('\nMedia Organized!\n')
        return None

    def on_press_organize_media(self):
        """ Start organizing media """
        tl = threading.Thread(target=self.recursively_organize_shows_and_movies)
        tl.start()

    def progress_bar_appear(self):
        self.toggle_buttons_enabled()
        self.progress_bar.pack(side=BOTTOM)
        w = self.winfo_width()
        self.progress_bar.config(length=w-8)
        self.progress_bar['value'] = 0
        self.s.configure(style=self.style, text='\n\n')

    def progress_complete(self, message):
        self.toggle_buttons_enabled()
        self.progress_bar['value'] = 0
        self.s.configure(style=self.style, text=message)

    def toggle_buttons_enabled(self):
        if self.disable_buttons:
            self.buttons.enable()
            self.disable_buttons = False
        else:
            self.buttons.disable()
            self.disable_buttons = True

    def locate_media(self):
        settings = save_paths(CONFIG.settings_path)
        missing_path = False
        for name, path in settings['paths'].items():
            if path:
                setattr(CONFIG.paths, name, path)
        for path in CONFIG.paths.to_dict().values():
            if not path:
                missing_path = True
        if not missing_path:
            self.buttons.select_media.pack(side=TOP, padx=10, pady=10, fill=X)
