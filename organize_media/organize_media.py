import threading
import shutil
import os
import re
import json
import yaml
from tkinter import *
from tkinter.ttk import Progressbar, Style, Separator
from copy import deepcopy

from functionality.general_functions import tv_show_ep_from_file_name, tv_show_ep_from_folder_structure, \
    initcap_file_name, get_media_title
from functionality.mo_functions import get_user_set_path, save_paths
from functionality.data import CONFIG, user_settings_template, ImageData, Images
from functionality.ui import Buttons


SETTINGS_PATH = 'settings/config.yaml'


class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info', bg='#ffffff', fg='#000000'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.bg = bg
        self.fg = fg
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tw, text=self.text, justify='left',
                      background=self.bg, foreground=self.fg, relief='solid', borderwidth=1,
                      wraplength=self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()


class OrganizeMedia(Tk):
    """ Utility GUI Tool, used to rename and organize media files -
        such as Movies and TV Shows - into appropriate folders. """

    def __init__(self):
        Tk.__init__(self)
        self.settings = self.__get_user_settings()
        self.title(CONFIG.title)
        self.iconbitmap('Images/organize_media.ico')
        self.config(bg=CONFIG.colors.main)

        self.on_startup()

        self.geometry('{w}x{h}+{x}+{y}'.format(**CONFIG.geometry.__dict__))
        self.configure(bg=CONFIG.colors.main)
        ''' Filter media will contain a dictionary like:
            {path: {file_name: name, title: title, kind: kind, ...}}'''
        self.filtered_media = {}
        self.all_media_info = {}
        self.disable_buttons = False

        # Images
        self.images = Images()
        self.images.populate()

        # Frames
        self.left_frame = Frame(self, bg=CONFIG.colors.main)
        self.left_frame.bind('<Destroy>', self.cache_info)  # Used to cache info when exiting the application
        self.status_bar = Canvas(self, bg=CONFIG.colors.sub, bd=0, highlightthickness=0,
                                 width=CONFIG.geometry.w, height=0, relief=SUNKEN)
        self.status_bar.pack(side=BOTTOM, fill=X)
        self.left_frame.pack(side=LEFT, fill=Y, ipadx=14, ipady=14)

        self.middle_canvas = Canvas(self, bg=CONFIG.colors.sub, bd=2, highlightthickness=0, relief=SUNKEN)
        self.canvas_frame = Frame(self.middle_canvas, bg=CONFIG.colors.sub)
        self.bind('<Configure>', self.mid_canvas_dim)
        self.middle_canvas.create_window((0, 0), window=self.canvas_frame, anchor=NW)
        y_scroll_bar = Scrollbar(self, command=self.middle_canvas.yview, orient=VERTICAL)
        x_scroll_bar = Scrollbar(self, command=self.middle_canvas.xview, orient=HORIZONTAL)
        self.middle_canvas.config(yscrollcommand=y_scroll_bar.set, xscrollcommand=x_scroll_bar.set)
        y_scroll_bar.pack(side=RIGHT, fill=Y)
        x_scroll_bar.pack(side=BOTTOM, fill=X)
        self.middle_canvas.pack(side=LEFT, fill=BOTH, expand=True, ipadx=4)
        self.bind_all("<MouseWheel>", self._on_mousewheel)

        # Buttons
        self.buttons = Buttons(self.left_frame)
        self.buttons.init()
        self.buttons.locate_media.button.config(command=self.locate_media)
        self.buttons.select_media.button.config(command=self.on_press_select_media)
        self.buttons.organize.button.config(command=self.on_press_organize_media)
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
        self.progress_bar = Progressbar(self.status_bar, style=self.style, length=w-8)
        self.progress_bar.bind('<Configure>', self.on_progress_bar_adjust)
        # self.progress_bar.pack(side=BOTTOM)
        # self.status_bar.pack_forget()

        self.buttons.organize.pack_forget()
        if not self.settings['paths'].get('downloads'):
            self.buttons.select_media.pack_forget()

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

    def on_first_locate_media(self, widgets):
        self.settings = save_paths(SETTINGS_PATH)
        if self.settings['paths'].get('downloads'):
            for w in widgets:
                w.destroy()

    def on_startup(self):
        if not self.settings['paths'].get('downloads'):
            frame = Frame(self, bg=CONFIG.colors.main)
            lbl1 = Label(frame, text='Sup,', bg=CONFIG.colors.main, fg=CONFIG.colors.alt,
                         font=CONFIG.fonts.xxlarge)
            lbl2 = Label(frame, text='Start by locating your media', wraplength=450,
                         bg=CONFIG.colors.main, fg='#%02x%02x%02x' % (180, 53, 240), font=CONFIG.fonts.xlarge)
            b = Button(frame, image=ImageData('', 'Images/dir.png', 94, 94).get(),
                       bg=CONFIG.colors.main, relief=RAISED, cursor='hand2')
            b.config(command=lambda x=(lbl1, frame, b): self.on_first_locate_media(x))

            frame.pack(ipadx=20)
            lbl1.pack(fill=X, pady=30)
            b.pack()
            lbl2.pack(fill=X, pady=30)

            self.wait_window(b)

    def on_progress_bar_adjust(self, event):
        """ Handles resizing progress bar, when the app is resized """
        self.progress_bar.config(length=self.winfo_width()-8)

    def cache_info(self, event):
        """ Handles resizing progress bar, when the app is resized """
        cache = dict()
        cache['geometry'] = {
            'w': self.winfo_width(),
            'h': self.winfo_height(),
            'x': self.winfo_rootx(),
            'y': self.winfo_rooty(),
        }
        os.makedirs('settings', exist_ok=True)
        with open('settings/cache', 'w') as file:
            json.dump(cache, file, indent=2)

    def mid_canvas_dim(self, event):
        """ Handles resizing of the 'Selected Media' portion of the app, when the app is resized """
        self.middle_canvas.configure(
            scrollregion=self.middle_canvas.bbox("all"),
            width=self.winfo_width(),
            height=self.winfo_height()
        )

    def _on_mousewheel(self, event):
        x, y = self.winfo_pointerxy()
        canvas = self.winfo_containing(x, y)
        widget_path = str(canvas.master)
        if widget_path == '.' or widget_path.startswith('.!canvas2') or widget_path.startswith('.filterwindow'):
            self.middle_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def get_media_info_from_paths(self, paths):
        """ Gets all media information from media files in the given paths

        :param paths: A list of paths to media files
        :return: A dictionary of information about each file
        """
        self.progress_bar_appear()
        self.progress_bar['maximum'] = len([file for path in paths
                                            for x, y, files in os.walk(path)
                                            for file in files
                                            if file.split('.')[-1] in self.settings['media_extensions']])
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
                    if extension in self.settings['media_extensions'] and os.path.isfile(current_file_path):
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

        :param all_media: The dictionary of all the media to filter
        :return: Filtered media
        """
        self.filtered_media = deepcopy(all_media)

        def upon_select(widget):
            d = widget['destination']
            fp = widget['file_path']
            # Add or remove files from list when they are toggled
            if widget['button'].var.get():
                if fp not in self.filtered_media[d]:
                    self.filtered_media[d][fp] = all_media[d][fp]
                    widget['button']['bg'] = CONFIG.colors.sub
            else:
                if fp in self.filtered_media[d]:
                    del self.filtered_media[d][fp]
                    widget['button']['bg'] = CONFIG.colors.main

        def toggle_all(x):
            button, kind, files_dict = x
            deselect_image = self.images.deselect
            select_image = self.images.select
            # Toggle each item in the dictionary based on the toggle
            toggle = True if str(button['image']) == str(select_image) else False
            for file, widget in files_dict.items():
                widget['button'].var = BooleanVar(value=toggle)
                widget['button']['variable'] = widget['button'].var
                upon_select(widget)
            if toggle:
                button['image'] = deselect_image
                if self.toggle_all_buttons[kind] == button:
                    for title, b in self.toggle_title_buttons[kind].items():
                        b['image'] = deselect_image
            else:
                button['image'] = select_image
                if self.toggle_all_buttons[kind] == button:
                    for title, b in self.toggle_title_buttons[kind].items():
                        b['image'] = select_image

            if self.toggle_all_buttons[kind] != button:
                off_title_buttons = [str(btn['image']) for t, btn in self.toggle_title_buttons[kind].items()
                                     if str(btn['image']) == str(select_image)]
                if off_title_buttons:
                    self.toggle_all_buttons[kind]['image'] = select_image
                else:
                    self.toggle_all_buttons[kind]['image'] = deselect_image

        def collapse_show(checklist_frame):
            if checklist_frame.winfo_viewable():
                checklist_frame.pack_forget()
            else:
                checklist_frame.pack(fill=X)

        def create_checklist(frame, files):
            kind_mapping = {'TV Show': 'TV Shows', 'Movie': 'Movies'}
            self.toggle_all_buttons = {k: {} for k in kind_mapping.keys()}
            self.toggle_title_buttons = {k: {} for k in kind_mapping.keys()}
            for folder_path, info in files.items():
                destination_frame = Frame(frame, bg=CONFIG.colors.main, bd=1, relief=RIDGE)
                destination_frame.pack(side=LEFT, padx=4, pady=4, anchor=N)
                destination_title = Label(destination_frame, text=folder_path, anchor=NW, justify=LEFT,
                                          bg=CONFIG.colors.main, fg=CONFIG.colors.font, font=CONFIG.fonts.medium)
                destination_title.pack(side=TOP, fill=X, anchor=W)
                Separator(destination_frame).pack(side=TOP, fill=X)
                sections = sorted(list(set([i['kind'] for f, i in info.items()])), reverse=True)
                for kind in sections:
                    kind_dict = dict()
                    if sections.index(kind) > 0:
                        # Add a separator between shows and movies
                        Separator(destination_frame).pack(fill=X, pady=8)
                    media_type_frame = Frame(destination_frame, bg=CONFIG.colors.main)
                    media_type_frame.pack(side=TOP, fill=X, anchor=NW)
                    # Toggle everything for each 'Kind'
                    self.toggle_all_buttons[kind] = Button(media_type_frame, cursor='hand2',
                                                           image=self.images.deselect,
                                                           relief=FLAT, bg=CONFIG.colors.main)
                    self.toggle_all_buttons[kind].pack(side=LEFT, anchor=NW)
                    media_type_label = Label(media_type_frame, text=kind_mapping[kind], font=CONFIG.fonts.small, anchor=NW,
                                             width=50, bg=CONFIG.colors.main, fg=CONFIG.colors.font, justify=LEFT)
                    media_type_label.pack(side=LEFT, fill=X)
                    media_content_frame = Frame(destination_frame, bg=CONFIG.colors.main, bd=2, relief=SUNKEN)
                    media_content_frame.pack(side=TOP, fill=X, anchor=NW)
                    if kind == 'Movie':
                        movie_frame = Frame(destination_frame, bg=CONFIG.colors.main, bd=2, relief=SUNKEN)
                        movie_frame.pack(side=TOP, fill=X, anchor=NW)
                    for t in sorted(list(set([v['title'] for k, v in info.items() if v['kind'] == kind]))):
                        dictionary = dict()
                        if kind == 'TV Show':
                            show_frame = Frame(media_content_frame, bg=CONFIG.colors.main)
                            show_frame.pack(side=TOP, fill=X, anchor=NW)
                            show_title_frame = Frame(show_frame, bg=CONFIG.colors.special)
                            show_title_frame.pack(side=TOP, fill=X, anchor=NW)
                            # Toggle everything for each TV Show title
                            self.toggle_title_buttons[kind][t] = Button(show_title_frame,
                                                                        image=self.images.deselect,
                                                                        text='deselect', cursor='hand2', relief=FLAT,
                                                                        bg=CONFIG.colors.main)
                            self.toggle_title_buttons[kind][t].pack(side=LEFT, fill=Y)
                            show_title_button = Button(show_title_frame, text=t, cursor='hand2',
                                                       font=CONFIG.fonts.small, anchor=W, bd=2, relief=RAISED,
                                                       bg=CONFIG.colors.main, fg=CONFIG.colors.font,
                                                       justify=LEFT)
                            show_title_button.pack(side=LEFT, fill=X, expand=True, anchor=W, padx=1, pady=1)
                            show_checklist_frame = Frame(show_frame, bg=CONFIG.colors.main, bd=2, relief=SUNKEN)
                            show_checklist_frame.pack(side=TOP, fill=X, anchor=NW)
                            show_title_button['command'] = lambda x=show_checklist_frame: collapse_show(x)
                            show_checklist_frame.pack_forget()
                            season_frames = {}
                            try:
                                for s in sorted(list(set([v['season'] for k, v in info.items() if v['title'] == t]))):
                                    season_frames[s] = Frame(show_checklist_frame, bg=CONFIG.colors.main)
                                    season_frames[s].pack(side=TOP, fill=X, anchor=NW)
                                    season = 'Season ' + str(s) if s != -1 else 'Extras'
                                    season_label = Label(season_frames[s], text=season, font=CONFIG.fonts.small,
                                                         bg=CONFIG.colors.alt, fg=CONFIG.colors.font)
                                    season_label.pack(side=TOP, fill=X, padx=1, pady=1)
                            except Exception as e:
                                print(t)
                                print([v['season'] for k, v in info.items() if v['title'] == t])
                                raise Exception(e)

                        for file_path, i in {f: i for f, i in info.items() if i['title'] == t}.items():
                            dictionary[file_path] = i
                            if kind == 'TV Show':
                                dictionary[file_path]['button'] = Checkbutton(season_frames[i['season']])
                            else:
                                dictionary[file_path]['button'] = Checkbutton(movie_frame)
                            dictionary[file_path]['button'].config(text=i['renamed_file_name'], fg=CONFIG.colors.font,
                                                                   onvalue=True, offvalue=False, anchor=NW,
                                                                   bg=CONFIG.colors.sub, font=CONFIG.fonts.xsmall,
                                                                   selectcolor=CONFIG.colors.main)
                            dictionary[file_path]['button'].var = BooleanVar(value=True)
                            dictionary[file_path]['button']['variable'] = dictionary[file_path]['button'].var
                            dictionary[file_path]['button']['command'] = lambda w=dictionary[file_path]: upon_select(w)
                            dictionary[file_path]['button'].pack(side=TOP, fill=X, anchor=NW, pady=1, padx=1)
                            dictionary[file_path]['destination'] = folder_path
                            kind_dict[file_path] = dictionary[file_path]
                        if kind == 'TV Show':
                            self.toggle_title_buttons[kind][t]['command'] = lambda d=(self.toggle_title_buttons[kind][t]
                                                                                      , kind, dictionary): toggle_all(d)
                    self.toggle_all_buttons[kind]['command'] = lambda d=(self.toggle_all_buttons[kind], kind,
                                                                         kind_dict): toggle_all(d)

        main_frame = Frame(self.canvas_frame, bg=CONFIG.colors.sub, name='filterwindow')
        main_frame.pack(fill=BOTH)
        create_checklist(main_frame, files=all_media)

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
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)
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
                self.organize_button_appear()
            else:
                self.organize_button_disappear()

    def on_press_organize_media(self):
        """ Start organizing media """
        tl = threading.Thread(target=self.recursively_organize_shows_and_movies)
        tl.start()

    def organize_button_appear(self):
        self.buttons.organize.pack(side=TOP, padx=10, pady=10, fill=X)

    def organize_button_disappear(self):
        self.buttons.organize.pack_forget()

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
        self.settings = save_paths(SETTINGS_PATH)
        if self.settings['paths'].get('downloads'):
            self.buttons.select_media.pack(side=TOP, padx=10, pady=10, fill=X)


app = OrganizeMedia()
app.mainloop()
