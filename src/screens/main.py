import threading
import shutil
import os
import re
import json
import time
from tkinter import *
from tkinter.ttk import Progressbar, Style

from src.components.ui import ButtonGroup, CheckBoxes, OMButton
from src.funcs.general import tv_show_ep_from_file_name, tv_show_ep_from_folder_structure, \
    initcap_file_name, get_media_title
from src.funcs.user_configuration import get_user_set_path, save_paths
from src.components.data import CONFIG, Images


class Main(Frame):
    def __init__(self, app, bg=CONFIG.colors.main, *args, **kwargs):
        """
        Args:
            app (Toplevel):
        """
        Frame.__init__(self, app, bg=bg, *args, **kwargs)
        app.geometry(CONFIG.geometry)
        # Images
        self.images = Images()

        ''' Filter media will contain a dictionary like:
                        {path: {file_name: name, title: title, kind: kind, ...}}'''
        self.all_media_info = dict()
        self.disable_buttons = False

        # Frames
        self.left_frame = Frame(self, bg=CONFIG.colors.main, bd=2, relief=RAISED)
        self.bind('<Destroy>', self.__on_destroy)  # Used to cache info when exiting the application
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
            file_name for path in paths
            for x, y, files in os.walk(path)
            for file_name in files
            if file_name.split('.')[-1] in CONFIG.media_extensions
        ])
        self.progress_bar['value'] = 0
        self.s.configure(style=self.style, text='Getting media info...')
        file_info = {}
        # Get a list of files to gather info for, and extract info from the local file
        for folder_path in paths:
            file_info[folder_path] = {}
            for path, folders, files in sorted(os.walk(folder_path)):
                for file in sorted(files):
                    current_file_path = os.path.join(path, file)
                    extension = file.split('.')[-1]
                    # If its a media file
                    if extension in CONFIG.media_extensions and os.path.isfile(current_file_path):
                        renamed_file = initcap_file_name(file)
                        file_folder_path = os.path.dirname(current_file_path)
                        bottom_folder = os.path.basename(file_folder_path)
                        # Split the file's path by the folder_path to get the folders inside of the main folder
                        if folder_path != file_folder_path:
                            split_path = [x for x in path.split(folder_path) if x]
                            # This is just making sure the string doesn't start with a slash
                            top_folder = split_path[-1] if split_path[-1][0] not in ['\\', '/'] \
                                else split_path[-1][1:]
                            top_folder = top_folder.split('\\')[0].split('/')[0]
                            top_folder_title = str(get_media_title(None,
                                                                   initcap_file_name(top_folder.replace('.', ' ')))
                                                   ).title()
                        else:
                            bottom_folder = None
                            top_folder_title = None

                        # Use the Season / Episode extracted based on the path,
                        # if it could not be extracted from the file name
                        tv_show_episode, season, episode = tv_show_ep_from_file_name(renamed_file)
                        s, e = tv_show_ep_from_folder_structure(current_file_path)
                        t = None
                        if not season and s:
                            season = s
                            t = top_folder_title
                        if not episode and e:
                            episode = e
                            t = top_folder_title

                        # Set the kind and season based on the season/episode extracted
                        if tv_show_episode or (season or season == 0) or (episode or episode == 0):
                            kind = 'TV Show'
                            # Assume it is the first season if there is no season extracted,
                            # but an episode was extracted, and there is a top folder
                            if not (season or season == 0) and (episode or episode == 0) and t:
                                season = 1
                            # If the folder containing the show has 'extras' in the name,
                            # then it is safe to assume that this is an extra episode
                            if 'extras' in str(bottom_folder).lower():
                                season = -1  # Extras are identified as season -1
                            # Assume it is a movie if it extracted only an episode; i.e. Star Wars Episode 1
                            elif not (season or season == 0) and (episode or episode == 0) and not t:
                                kind = 'Movie'
                        else:
                            kind = 'Movie'

                        title = get_media_title(tv_show_episode, renamed_file)
                        years = re.findall(r'20\d\d|19\d\d', file)
                        year = int(years[0]) if years else None

                        # Set the title for the Show/Movie based the show/season/episode info extracted
                        if kind == 'TV Show':
                            if (season or season == 0) and season != -1 and (episode or episode == 0):
                                title = top_folder_title if top_folder_title else title
                                renamed_file_name = f'{title} - ' \
                                                    f'S{ "0" + str(season) if season < 10 else season}' \
                                                    f'E{ "0" + str(episode) if episode < 10 else episode}'
                            else:
                                renamed_file_name = renamed_file.split('.')[0]
                        else:
                            renamed_file_name = title

                        file_info[folder_path][current_file_path] = {
                            'title': title, 'renamed_file_name': renamed_file_name, 'file_name': file,
                            'file_path': current_file_path, 'top_folder_title': top_folder_title,
                            'kind': kind, 'year': year, 'season': season, 'episode': episode, 'selected': True
                        }
                        self.progress_bar['value'] += 1
                        self.s.configure(style=self.style,
                                         text=f'Got info for {file}\nIn the {folder_path} directory\n')
            if not file_info[folder_path]:
                del file_info[folder_path]

        top_folder_dict = {}
        for folder_path, info in file_info.items():
            for file_path, i in info.items():
                if i['top_folder_title']:
                    if i['top_folder_title'] not in top_folder_dict:
                        top_folder_dict[i['top_folder_title']] = {'title_list': [i['title']],
                                                                  'kind': i['kind'],
                                                                  'year': i['year']}
                    elif i['top_folder_title'] in top_folder_dict:
                        if i['title'] not in top_folder_dict[i['top_folder_title']]['title_list']:
                            top_folder_dict[i['top_folder_title']]['title_list'].append(i['title'])
                        if i['kind'] == 'TV Show':
                            top_folder_dict[i['top_folder_title']]['kind'] = i['kind']
                        if i['year']:
                            top_folder_dict[i['top_folder_title']]['year'] = i['year']

        for top_folder, info in top_folder_dict.items():
            top_folder_dict[top_folder]['num_unique_titles'] = len(info['title_list'])
        for folder_path, info in file_info.items():
            for file_path, i in info.items():
                if i['top_folder_title']:
                    file_info[folder_path][file_path]['kind'] = top_folder_dict[i['top_folder_title']]['kind']
                    file_info[folder_path][file_path]['year'] = top_folder_dict[i['top_folder_title']]['year']
                    if not file_info[folder_path][file_path]['season'] \
                            and file_info[folder_path][file_path]['kind'] == 'TV Show':
                        file_info[folder_path][file_path]['season'] = -1
                        file_info[folder_path][file_path]['renamed_file_name'] = initcap_file_name(i['file_name']
                                                                                                   ).split('.')[0]
                    if top_folder_dict[i['top_folder_title']]['num_unique_titles'] > 1:
                        file_info[folder_path][file_path]['title'] = i['top_folder_title']
        del top_folder_dict
        self.progress_complete('Gathered Media!')
        return file_info

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

        self.all_media_info = self.get_media_info_from_paths(folder_paths)

        if not self.all_media_info:
            self.progress_bar_appear()
            self.progress_complete('\nNo Media Detected...\n')
            self.buttons.organize.pack_forget()
        else:
            self.filter_window()
            self.buttons.organize.pack(side=TOP, padx=10, pady=10, fill=X)

    def filter_window(self):
        """ The filter window that appears to filter the media files to be sorted. """

        def on_toggle_off(metadata):
            """ A function that is passed to the CheckBox,
                and executes when the CheckBox is toggled off.

            Args:
                metadata (dict): The metadata from the CheckBox;
                    CheckBox expects to pass metadata to this function
            """
            origin = metadata.get('origin_dir')
            file_path = metadata.get('file_path')
            self.all_media_info[origin][file_path].update({'selected': False})

        def on_toggle_on(metadata):
            """ A function that is passed to the CheckBox,
                and executes when the CheckBox is toggled on.

            Args:
                metadata (dict): The metadata from the CheckBox;
                    CheckBox expects to pass metadata to this function
            """
            origin = metadata.get('origin_dir')
            file_path = metadata.get('file_path')
            self.all_media_info[origin][file_path].update({'selected': True})

        def reform_files_dict():
            """ Reforms the media files dict, to a format that can be used to generate CheckBoxes.
                Here we also pass our on_toggle_off and on_toggle_on functions,
                as well as any additional metadata we need the CheckBox to have.

            Args:
                files (dict): The dict of all media files to be reformed

            Returns: The reformed files dict
            """
            new_files = dict()
            for folder_dir, info in self.all_media_info.items():
                # Reduce the display of the folder path to the last two folders, maximum
                folder_path = os.path.normpath(folder_dir).split(os.sep)
                if len(folder_path) > 1:
                    folder = os.path.join(*folder_path[-2:])
                else:
                    folder = os.path.join(*folder_path)
                new_files.setdefault(folder, {})
                for file_path, file_info in info.items():
                    kind = f"{file_info['kind']}s"
                    title = file_info.get('title')
                    season_num = file_info.get('season')
                    file_info['origin_dir'] = folder_dir
                    file_info['on_toggle_off'] = on_toggle_off
                    file_info['on_toggle_on'] = on_toggle_on
                    if season_num is not None:
                        season = 'Season ' + str(season_num) if season_num != -1 else 'Extras'
                        new_files[folder].setdefault(kind, {})
                        new_files[folder][kind].setdefault(title, {})
                        new_files[folder][kind][title].setdefault(season, [])
                        new_files[folder][kind][title][season].append(file_info)
                        # Sort the files by the new name
                        new_files[folder][kind][title][season] = list(sorted(
                            new_files[folder][kind][title][season], key=lambda f: f['renamed_file_name']))
                    else:
                        new_files[folder].setdefault(kind, [])
                        new_files[folder][kind].append(file_info)
                        # Sort the files by the new name
                        new_files[folder][kind] = list(sorted(
                            new_files[folder][kind], key=lambda f: f['renamed_file_name']))

            return new_files

        checkboxes = CheckBoxes(self.canvas_frame, reform_files_dict())
        checkboxes.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)

    def recursively_organize_shows_and_movies(self, delete_folders=True):
        dl_path = CONFIG.paths.downloads
        media_path = CONFIG.paths.media
        folders_to_delete = []
        self.progress_bar_appear()
        self.progress_bar['maximum'] = len([
            p for inf in self.all_media_info.values()
            for p, det in inf.items()
            if det.get('selected')
        ])
        self.progress_bar['value'] = 0

        for folder_path, i in self.all_media_info.items():
            for file_path, info in i.items():
                if not info['selected']:
                    continue
                path = os.path.dirname(file_path)
                file = os.path.basename(file_path)
                extension = file.split('.')[-1]
                skip = False
                # Route for TV Shows
                if info['kind'] == 'TV Show':
                    season_folder = 'Extras' if info["season"] == -1 else f'Season {info["season"]}'
                    output_folder = os.path.join(media_path, 'TV Shows', info['title'], season_folder)
                # Route for Movies
                else:
                    output_folder = os.path.join(media_path, 'Movies')
                output_path = os.path.join(output_folder, file)
                renamed_file = info['renamed_file_name'] + '.' + extension
                renamed_file_path = os.path.join(output_folder, renamed_file)
                # Create output folder if it does not exist
                os.makedirs(output_folder, exist_ok=True)
                # Move and then rename file
                if not os.path.exists(output_path) and not os.path.exists(renamed_file_path):
                    shutil.move(file_path, output_path)
                    os.rename(output_path, renamed_file_path)
                    status_message = f'Moved & Renamed {info["kind"].title()}:\nFrom: {file}\nTo: {renamed_file}'
                    # Update status and increment progress bar to show that the file has moved

                elif not os.path.exists(renamed_file_path):
                    os.rename(output_path, renamed_file_path)
                    # Update status and increment progress bar to show that the file has moved
                    status_message = f'File exists in {output_folder},' \
                                     f' Renamed {info["kind"].title()}:\nFrom: {file}\nTo: {renamed_file}'
                else:
                    skip = True
                    status_message = f'Skipping: {file}\nFile exists in {output_folder}:\n{renamed_file_path}'
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
