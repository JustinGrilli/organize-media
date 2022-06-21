import threading
import shutil
import os
import re
import json
from tkinter import *
from tkinter.ttk import Progressbar, Style
from copy import deepcopy

from src.components.ui import ButtonGroup, CheckBoxes
from src.funcs.general import tv_show_ep_from_file_name, tv_show_ep_from_folder_structure, \
    initcap_file_name, get_media_title
from src.funcs.user_configuration import get_user_set_path, save_paths
from src.components.data import CONFIG, Images


SETTINGS_PATH = 'settings/config.yaml'


class Main(Frame):
    def __init__(self, app, bg=CONFIG.colors.main, *args, **kwargs):
        Frame.__init__(self, app, bg=bg, *args, **kwargs)
        app.geometry(CONFIG.geometry)
        # Images
        self.images = Images()

        ''' Filter media will contain a dictionary like:
                        {path: {file_name: name, title: title, kind: kind, ...}}'''
        self.filtered_media = {}
        self.all_media_info = {}
        self.disable_buttons = False

        # Frames
        self.left_frame = Frame(self, bg=CONFIG.colors.main, bd=2, relief=RAISED)
        self.bind('<Destroy>', self.cache_info)  # Used to cache info when exiting the application
        self.canvas_frame = Frame(self, bg=CONFIG.colors.main)
        self.status_bar = Canvas(self, bg=CONFIG.colors.sub, bd=0, highlightthickness=0,
                                 width=self.winfo_width(), height=0, relief=SUNKEN)
        self.status_bar.pack(side=BOTTOM, fill=X)
        self.left_frame.pack(side=LEFT, fill=Y, ipadx=14, ipady=14)
        self.canvas_frame.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)

        # Buttons
        self.buttons = ButtonGroup(self.left_frame)
        self.buttons.locate_media.config(command=self.locate_media)
        self.buttons.select_media.config(command=self.on_press_select_media)
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
        if not app.settings['paths'].get('downloads'):
            self.buttons.select_media.pack_forget()

    def on_progress_bar_adjust(self, event):
        """ Handles resizing progress bar, when the app is resized """
        self.progress_bar.config(length=self.winfo_width()-8)

    def cache_info(self, event):
        """ Handles resizing progress bar, when the app is resized """
        cache = dict()
        cache['geometry'] = {
            'w': self.master.winfo_width(),
            'h': self.master.winfo_height(),
            'x': self.master.winfo_x(),
            'y': self.master.winfo_y(),
        }
        os.makedirs('settings', exist_ok=True)
        with open('settings/cache', 'w') as file:
            json.dump(cache, file, indent=2)

    def get_media_info_from_paths(self, paths):
        """ Gets all media information from media files in the given paths

        :param paths: A list of paths to media files
        :return: A dictionary of information about each file
        """
        self.progress_bar_appear()
        self.progress_bar['maximum'] = len([file for path in paths
                                            for x, y, files in os.walk(path)
                                            for file in files
                                            if file.split('.')[-1] in self.master.settings['media_extensions']])
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
                    if extension in self.master.settings['media_extensions'] and os.path.isfile(current_file_path):
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
                            'kind': kind, 'year': year, 'season': season, 'episode': episode}
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

    def media_files_info(self, folder_paths=[]):
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

        :param folder_paths: The path to your media files
        :return: A dictionary of information about each file
        """
        self.all_media_info = self.get_media_info_from_paths(folder_paths)

        if not self.all_media_info:
            self.progress_bar_appear()
            self.progress_complete('\nNo Media Detected...\n')
            return 'No Media'

        else:
            self.filter_window(self.all_media_info)

    def filter_window(self, all_media):
        """ The filter window that appears to filter the media files to be sorted.

        Args:
            all_media (dict): The dictionary of all the media to filter

        Returns: Filtered media
        """
        self.filtered_media = deepcopy(all_media)

        def on_toggle_off(metadata):
            """ A function that is passed to the CheckBox,
                and executes when the CheckBox is toggled off.

            Args:
                metadata (dict): The metadata from the CheckBox;
                    CheckBox expects to pass metadata to this function
            """
            origin = metadata.get('origin_dir')
            file_path = metadata.get('file_path')
            if self.filtered_media.get(origin, {}).get(file_path):
                del self.filtered_media[origin][file_path]

        def on_toggle_on(metadata):
            """ A function that is passed to the CheckBox,
                and executes when the CheckBox is toggled on.

            Args:
                metadata (dict): The metadata from the CheckBox;
                    CheckBox expects to pass metadata to this function
            """
            origin = metadata.get('origin_dir')
            file_path = metadata.get('file_path')
            if not self.filtered_media.get(origin, {}).get(file_path):
                self.filtered_media[origin][file_path] = all_media[origin][file_path]

        def reform_files_dict(files):
            """ Reforms the media files dict, to a format that can be used to generate CheckBoxes.
                Here we also pass our on_toggle_off and on_toggle_on functions,
                as well as any additional metadata we need the CheckBox to have.

            Args:
                files (dict): The dict of all media files to be reformed

            Returns: The reformed files dict
            """
            new_files = dict()
            for folder_dir, info in files.items():
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

        checkboxes = CheckBoxes(self.canvas_frame, reform_files_dict(all_media))
        checkboxes.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)

    def recursively_organize_shows_and_movies(self, delete_folders=True):
        dl_path = get_user_set_path(SETTINGS_PATH, 'downloads')
        media_path = get_user_set_path(SETTINGS_PATH, 'media')
        folders_to_delete = []
        self.progress_bar_appear()
        self.progress_bar['maximum'] = len(self.filtered_media.keys())
        self.progress_bar['value'] = 0

        for folder_path, i in self.filtered_media.items():
            for file_path, info in i.items():
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

    def todo_window(self):

        def upon_select(widget):
            if widget['button'].var.get():
                if widget['todo'] not in self.final_todo_list:
                    self.final_todo_list.append(widget['todo'])
                    widget['button']['bg'] = CONFIG.colors.alt
            else:
                if widget['todo'] in self.final_todo_list:
                    self.final_todo_list.remove(widget['todo'])
                    widget['button']['bg'] = CONFIG.colors.main

        def on_submit():
            self.toggle_buttons_enabled()
            submit_button.destroy()
            main_frame.destroy()

        main_frame = Frame(self.canvas_frame, bg=CONFIG.colors.main, bd=1, relief=RAISED)
        main_frame.pack(padx=8, pady=90)
        self.toggle_buttons_enabled()

        self.final_todo_list = []

        todo_list = {
            'downloads': 'Downloads',
            'media': 'Movies and TV Shows'
        }
        Label(main_frame, text='Which folders would you like to organize?', font=CONFIG.fonts.medium,
              bg=CONFIG.colors.main, fg=CONFIG.colors.font).pack(side=TOP, fill=X, ipady=20, ipadx=20)

        options_frame = Frame(main_frame, bg=CONFIG.colors.main, bd=2, relief=SUNKEN)
        options_frame.pack(side=TOP)

        dictionary = dict()
        for i, desc in todo_list.items():
            dictionary[i] = {'button': Checkbutton(options_frame, text=desc, onvalue=True, offvalue=False,
                                                   font=CONFIG.fonts.xsmall,
                                                   anchor=NW, bg=CONFIG.colors.alt, fg=CONFIG.colors.font,
                                                   selectcolor=CONFIG.colors.main)}
            dictionary[i]['button'].var = BooleanVar(value=True)
            self.final_todo_list.append(i)
            dictionary[i]['button']['variable'] = dictionary[i]['button'].var
            dictionary[i]['button']['command'] = lambda w=dictionary[i]: upon_select(w)
            dictionary[i]['button'].pack(side=TOP, fill=X, padx=1, pady=1)
            dictionary[i]['todo'] = i
        submit_button = Button(main_frame, text='Select', command=on_submit, font=CONFIG.fonts.small,
                               bg=CONFIG.colors.special, fg=CONFIG.colors.font)
        submit_button.pack(side=BOTTOM, pady=20)
        self.wait_window(main_frame)
        return self.final_todo_list

    def on_press_select_media(self):
        """
        When you press "Select Media" the following should happen:
            - Popup window displaying a checklist of options for things that will happen:
                - Move media from Downloads to Movies and TV Shows folders
                - Organize media already in the Movie and TV Shows folders
            - After choosing one or both options a Filter window will appear
            - The filter window will have two possible columns; One of downloads and one for existing media
            - Once files are selected, a button will appear to start organizing
        """
        # Reset Selected Media
        for item in self.canvas_frame.children.values():
            item.pack_forget()

        options = self.todo_window()
        if options:
            paths = []
            for option in options:
                if option == 'media':
                    path = get_user_set_path(SETTINGS_PATH, option)
                    paths.append(os.path.join(path, 'TV Shows'))
                    paths.append(os.path.join(path, 'Movies'))
                else:
                    paths.append(get_user_set_path(SETTINGS_PATH, option))

            outcome = self.media_files_info(folder_paths=paths)
            if outcome != 'No Media':
                self.buttons.organize.pack(side=TOP, padx=10, pady=10, fill=X)
            else:
                self.buttons.organize.pack_forget()

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
        self.master.settings = save_paths(SETTINGS_PATH)
        if self.master.settings['paths'].get('downloads'):
            self.buttons.select_media.pack(side=TOP, padx=10, pady=10, fill=X)
