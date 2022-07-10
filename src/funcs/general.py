import re
import os
from pathlib import Path
from datetime import date


SEASON_EPISODE_PATTERNS = [
    # Season 1 Episode 1 or Season 01 Episode 01
    r'season[^\w\d]\d{1,2}[^\w\d]episode[^\w\d]\d{1,2}',
    # s1e1e2 or s01e01e02
    r's\d{1,2}e\d{1,2}e\d{1,2}',
    # s1e1 or s01e01
    r's\d{1,2}e\d{1,2}',
    # s1 e1 or s01 e01
    r's\d{1,2}[^\w\d]e\d{1,2}',
    # 1x1 or 10x01
    r'\d{1,2}x\d{1,2}',
    # 101 or 1001
    r'\d{3,4}'
]
EPISODE_PATTERNS = [
    # Episode 1 or Episode 01
    r'episode[^\w\d]\d{1,2}',
    # e1e2 or e01e02
    r'e\d{1,2}e\d{1,2}',
    # e1 or e01
    r'e\d{1,2}',
    # x1 or x01
    r'x\d{1,2}',
    # 1 - 9999
    r'\d{1,4}'
]


def initcap_file_name(file_name):
    extension = file_name.split('.')[-1] if '.' in file_name else ''
    new_string = file_name.replace(extension, '')
    new_string = re.sub(r'[^\w\d()]+', ' ', new_string.title()).strip()
    if extension:
        new_string = f'{new_string}.{extension}'
    return new_string


def generate_show_patterns(show_pattern: str) -> str:
    # Start of line + show_pattern + end of line
    yield show_pattern.join([r'^(', r')$'])
    # Non word or num + show_pattern + end of line
    yield show_pattern.join([r'[^\w\d(](', r')$'])
    # Start of line + show_pattern + Non word or num
    yield show_pattern.join([r'^(', r')[^\w\d)]'])
    # Non word or num + show_pattern + Non word or num
    yield show_pattern.join([r'[^\w\d(](', r')[^\w\d)]'])


def get_show_season_and_episode(file_path: str) -> tuple[str, str, str]:

    def get_show_from_patterns(patterns):
        for media_pattern in patterns:
            for pattern in generate_show_patterns(media_pattern):
                found = re.findall(pattern, file_name, re.IGNORECASE)
                if found:
                    return found[0]
        return ''

    file_name = os.path.basename(file_path)
    # Determine the Season # from folders along the files directory
    show = get_show_from_patterns(SEASON_EPISODE_PATTERNS)
    season = ''
    episode = ''
    for f in os.path.split(os.path.dirname(file_path)):
        s = re.findall(r'season (\d+)', f, re.IGNORECASE)
        if s:
            season = s[0] if isinstance(s, list) else s
            if len(season) == 1:
                season = f'0{season}'

    # Parse the Season # and Episode # from show
    if show:
        nums = [
            n if len(n) > 1 else f'0{n}'
            for n in re.findall(r'\d+', show)
        ]
        if len(nums) == 3:
            return show, nums[0], f'{nums[1]}-{nums[2]}'
        if len(nums) == 2:
            return show, nums[0], nums[1]
        if len(nums) == 1:
            nums = [n for n in nums[0]]
            if len(nums) == 4:
                # show, '00', '00'
                return show, ''.join(nums[0:2]), ''.join(nums[2:4])
            if len(nums) == 3:
                # show, '0', '00'
                return show, nums[0], ''.join(nums[1:3])

    # If the show could not be determined by SEASON_EPISODE_PATTERNS,
    # but a season was parsed from folders along the files directory:
    # Get show from EPISODE_PATTERNS
    if not show and season:
        show = get_show_from_patterns(EPISODE_PATTERNS)

    # Parse the Episode # from show
    if show:
        nums = [
            n if len(n) > 1 else f'0{n}'
            for n in re.findall(r'\d+', show)
        ]
        if len(nums) == 2:
            return show, season, f'{nums[1]}-{nums[2]}'
        if len(nums) == 1:
            return show, season, nums[0]

    return show, season, episode


def get_file_title(file_name: str, show: str) -> str:
    if show:
        title = file_name.replace(show, '')
        title = initcap_file_name(title)
    else:
        title = initcap_file_name(file_name)
    title = re.sub(r'\.\w+$', r'', title)
    return title


def tv_show_ep_from_file_name(file_name):
    """ Finds the pattern of the TV Show, and number for the season and episode based on the pattern.

    Args:
        file_name (str): The file name to extract the tv show episode pattern and season from.
    
    Returns: The tv show pattern, tv show season number, and episode number.
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
        matches = re.findall(pattern, file_name, re.IGNORECASE)
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


def get_media_title(tv_show_episode, file_name) -> str:
    """ Extract the title from the file name.

    Args:
        tv_show_episode (str): The season/episode as it is defined in the file name
        file_name (str): The file name
    Returns: The title
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
                           r'[a-z:\- ]+\d?$|'
                           r'[a-z:\- ]+\d?\D\(\w+\)$|'
                           r'[a-z:\- ]+\d?\D\(\w]+\)\D|'
                           r'[a-z:\- ]+\d?\D|\d+[^\w\d]?'
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


if __name__ == '__main__':
    test_show = Path('This Test/Season 2/this.test.e30.avi')
    test_movie = 'This Test/this.test.1080p.avi'
    print(test_show.parts[0])
    se_ep, s, e = get_show_season_and_episode(test_show)
    print(se_ep, s, e)
    se_ep, s, e = get_show_season_and_episode(test_movie)
    print(se_ep, s, e)
