import re
import os
from datetime import date


def initcap_file_name(string):
    extension = string.split('.')[-1] if '.' in string else None
    if extension:
        new_string = string.replace(extension, '')
    else:
        new_string = string
    new_string = re.sub(r'[^a-zA-Z0-9()]', ' ', new_string)
    new_string = re.sub(' +', ' ', new_string)
    new_string = new_string.title()
    if extension:
        new_string = '.'.join([new_string, extension])
    return new_string.strip()


def tv_show_ep_from_file_name(file):
    """ Finds the pattern of the TV Show, and number for the season and episode based on the pattern.

    :param file: The file name to extract the tv show episode pattern and season from.
    :return: The tv show pattern, tv show season number, and episode number.
    """
    bad_nums = ['360', '480', '720', '1080', '264']
    tv_show_episode = None
    season = None
    episode = None
    # Search through the file name for the following patterns
    patterns = [
        # s1e1 or s01e01 or s01e01e02
        r'[^\w\d](s\d{1,2}e\d{1,2}e?\d{0,2})$|'
        r'^(s\d{1,2}e\d{1,2}e?\d{0,2})[^\w\d]|'
        r'[^\w\d](s\d{1,2}e\d{1,2}e?\d{0,2})[^\w\d]',
        # s1 e1 or s01 e01
        r'[^\w\d](s\d{1,2}[^\w\d]e\d{1,2})$|'
        r'^(s\d{1,2}[^\w\d]e\d{1,2})[^\w\d]|'
        r'[^\w\d](s\d{1,2}[^\w\d]e\d{1,2})[^\w\d]',
        # 1x01 or 10x01
        r'^(\d{1,2}x\d{1,2})[^\w\d]|'
        r'[^\w\d](\d{1,2}x\d{1,2})$|'
        r'[^\w\d](\d{1,2}x\d{1,2})[^\w\d]',
        # Season 1 Episode 1 or Season 01 Episode 01
        r'[^\w\d](season[^\w\d]\d{1,2}[^\w\d]episode[^\w\d]\d{1,2})$|'
        r'^(season[^\w\d]\d{1,2}[^\w\d]episode[^\w\d]\d{1,2})[^\w\d]|'
        r'[^\w\d](season[^\w\d]\d{1,2}[^\w\d]episode[^\w\d]\d{1,2})[^\w\d]',
        # 101 or 1001
        r'^(\d{3,4})[^\w\d]|'
        r'[^\w\d](\d{3,4})$|'
        r'[^\w\d](\d{3,4})[^\w\d]'
    ]
    current_year = date.today().year
    for pattern in patterns:
        matches = re.findall(pattern, file, re.IGNORECASE)
        # If the pattern returns matches
        if matches:
            if patterns.index(pattern) != 4:
                tv_show_episode = [x for x in matches[0] if x][0]
                nums = [int(x) for x in re.findall(r'\d+', tv_show_episode)]
                # tv_ep, season, episode(s)
                return tv_show_episode, nums[0], nums[1:] if len(nums) > 2 else nums[1]
            else:
                matches = [num for num in matches[0]
                           if num and int(num[-2:]) < 30 and num[-2:] != '00' and num not in bad_nums
                           and (int(num) < current_year-30 or int(num) > current_year)]
                if matches:
                    tv_show_episode = matches[0]
                    season = int(tv_show_episode[:-2])
                    episode = int(tv_show_episode[-2:])
                    return tv_show_episode, season, episode

    return tv_show_episode, season, episode


def tv_show_ep_from_folder_structure(file_path):
    """ Finds the pattern of the TV Show, and number for the season and episode based on the pattern.

    Args:
        file_path (str): The file path to extract the tv show episode pattern and season from.

    Returns: The tv show pattern, tv show season number, and episode number.
    """

    names = {
        'episode': os.path.basename(file_path),
        'season': os.path.basename(os.path.dirname(file_path))
    }
    # Search through the file name for the following patterns
    patterns = {
        'episode': [
            # e1 or e01
            r'[^\w\d](e\d{1,2})$|'
            r'^(e\d{1,2})[^\w\d]|'
            r'[^\w\d](e\d{1,2})[^\w\d]',
            # Episode 1 Episode 01
            r'[^\w\d]([episode[^\w\d]\d{1,2})$|'
            r'^(episode[^\w\d]\d{1,2})[^\w\d]|'
            r'[^\w\d](episode[^\w\d]\d{1,2})[^\w\d]'
        ],
        'season': [
            # s1 or s01
            r'[^\w\d](s\d{1,2})$|'
            r'^(s\d{1,2})[^\w\d]|'
            r'[^\w\d](s\d{1,2})[^\w\d]',
            # Season 1 Season 01
            r'[^\w\d]([season[^\w\d]\d{1,2})$|'
            r'^(season[^\w\d]\d{1,2})[^\w\d]|'
            r'[^\w\d](season[^\w\d]\d{1,2})[^\w\d]'
        ]
    }
    extractions = {'season': None, 'episode': None}
    for kind, file in names.items():
        for pattern in patterns[kind]:
            matches = re.findall(pattern, file, re.IGNORECASE)
            # If the pattern returns matches
            if matches:
                match = [x for x in matches[0] if x][0]
                extractions[kind] = [int(x) for x in re.findall(r'\d+', match)][0]

    return extractions['season'], extractions['episode']


def get_media_title(tv_show_episode, file_name):
    """ Extract the title from the file name.

    :param tv_show_episode: The season/episode as it is defined in the file name
    :param file_name: The file name
    :return: The title
    """
    clean_file_name = initcap_file_name(file_name)
    if tv_show_episode:
        # If the episode is the first part of the file name
        if clean_file_name.startswith(tv_show_episode):
            # If the tv show is not the entire file name
            if clean_file_name.split('.')[0].strip() != tv_show_episode:
                clean_file_name = clean_file_name.replace(f'{tv_show_episode} ', '').split('.')[0]
                return clean_file_name
            else:
                return clean_file_name
        else:
            return clean_file_name.split(f' {tv_show_episode}')[0].title()
    else:
        # The title should start with a string and stop at the first single digit
        title = re.findall(r'^('
                           r'[a-z:\- ]+[0-9]?$|'
                           r'[a-z:\- ]+[0-9]?[^\d]\([a-z]+\)$|'
                           r'[a-z:\- ]+[0-9]?[^\d]\([a-z]+\)[^\d]|'
                           r'[a-z:\- ]+[0-9]?[^\d]|[0-9]+[^\w\d]?'
                           r')', clean_file_name, re.IGNORECASE)
        title = re.sub(r'[^a-zA-Z0-9\-]', ' ', title[0]).strip() if title else None
        return title


def rename_all_media_in_directory(media_info):
    """ Renames all of the media files in the path

    :param media_info: Dict of all files to rename
    :return: None
    """
    for file, info in media_info.items():
        file_folder = os.path.dirname(info['path'])
        renamed_file_path = os.path.join(file_folder, info['file_name'] + file.split('.')[-1])
        if not os.path.exists(renamed_file_path):
            os.rename(info['path'], renamed_file_path)
    return None

