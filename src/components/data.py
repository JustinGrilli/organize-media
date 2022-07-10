import os
import json
import yaml
from pathlib import Path
from difflib import SequenceMatcher, Match

from PIL import Image, ImageTk
from dataclasses import dataclass, astuple, asdict, field
from src.funcs.general import get_file_title, get_show_season_and_episode


@dataclass
class MediaFile:
    path: str
    origin_dir: str
    parent_dir: str = None
    file_name: str = None
    file_rename: str = None
    type: str = None
    extension: str = None
    title: str = None
    season: int = None
    episode: int = None
    selected: bool = True

    def __post_init__(self):
        show, self.season, self.episode = get_show_season_and_episode(self.path)
        self.file_name = os.path.basename(self.path)
        self.extension = self.file_name.split('.')[-1].lower()
        self.title = get_file_title(self.file_name, show)
        # Get the file_rename
        if show:
            self.type = 'TV Show'
            self.file_rename = ' '.join([self.title, f's{self.season}e{self.episode}']) + f'.{self.extension}'
        else:
            self.type = 'Movie'
            self.file_rename = f'{self.title}.{self.extension}'
        # Get the parent_dir
        if self.origin_dir == self.path:
            self.parent_dir = Path(self.path).parts[-1]
        else:
            parent_dir = list()
            for part in list(Path(self.path).parts):
                if part not in list(Path(self.origin_dir).parts):
                    parent_dir.append(part)
            self.parent_dir = parent_dir[0]

    def select(self, *args, **kwargs):
        self.selected = True

    def deselect(self, *args, **kwargs):
        self.selected = False


@dataclass
class MediaContainer:
    title: str = None
    type: str = None
    media_files: list[MediaFile] = field(default_factory=list)

    def add_similar_media_file(self, media_file: MediaFile, thresh: float = 0.7):
        if not self.title:
            self.title = media_file.title
            self.type = media_file.type
            self.media_files.append(media_file)
            return True
        sameness_ratio = SequenceMatcher(None, self.title, media_file.title).ratio()
        if sameness_ratio >= thresh and self.type == media_file.type:
            self.media_files.append(media_file)
            same = list()
            for word in self.title.split(' '):
                if word in media_file.title.split(' '):
                    same.append(word)
            self.title = ' '.join(same)
            return True
        return False


class OMImage(ImageTk.PhotoImage):
    """
        Extends the funcs of ImageTk.PhotoImage.
        Allows PhotoImage fetching by path, and size declaration by width and height.
    """
    def __init__(self, path, width=64, height=64, **kw):
        self.path = path
        self.size = (width, height)
        self.image = self.__get_image()
        ImageTk.PhotoImage.__init__(self, self.image, **kw)

    def __get_image(self):
        with Image.open(self.path) as img:
            image = img.resize(self.size, Image.ANTIALIAS)
        return image

    def resize(self, width, height):
        self.__init__(self.path, width, height)


class Images:
    def __init__(self):
        self.locate_media: [OMImage] = OMImage('Images/dir.png')
        self.select_media: [OMImage] = OMImage('Images/filter.png')
        self.organize: [OMImage] = OMImage('Images/organize_media.png')
        self.deselect: [OMImage] = OMImage('Images/deselect.png', 24, 24)
        self.select: [OMImage] = OMImage('Images/select.png', 24, 24)
        self.arrow: [OMImage] = OMImage('Images/arrow.png', 24, 24)
        self.icon: [OMImage] = OMImage('Images/toolbar_icon.ico', 30, 30)


@dataclass
class Colors:
    main: str = '#141414'
    sub: str = '#232323'
    special: str = '#5c0f80'
    special_alt: str = '#b435f0'
    alt: str = '#3c6fc2'
    font: str = '#ffffff'


@dataclass
class Font:
    name: str = 'Ebrima'
    size: int = 11


@dataclass
class Fonts:
    xxsmall: tuple = astuple(Font())
    xsmall: tuple = astuple(Font(size=12))
    small: tuple = astuple(Font(size=13))
    medium: tuple = astuple(Font(size=14))
    large: tuple = astuple(Font(size=18))
    xlarge: tuple = astuple(Font(size=22))
    xxlarge: tuple = astuple(Font(size=40))


@dataclass
class Paths:
    downloads: str = ''
    media: str = ''

    def to_dict(self):
        return asdict(self)


@dataclass
class Geometry:
    w: int = 400
    h: int = 400
    x: int = 0
    y: int = 0

    def to_str(self):
        return '{w}x{h}+{x}+{y}'.format(**asdict(self))

    def to_tup(self):
        return astuple(self)

    def to_dict(self):
        return asdict(self)


@dataclass
class Settings:
    title: str = 'Organize Media'
    geometry: str = '1000x800+0+0'
    colors: [Colors] = Colors()
    fonts: [Fonts] = Fonts()
    media_extensions: set = field(default=set)
    paths: [Paths] = Paths()
    settings_path: str = 'settings/config.yaml'
    cache_path: str = 'settings/cache'


# Instantiate the Settings as CONFIG
_settings = {
    'media_extensions': {'mp4', 'mkv', 'avi', 'flv', 'wmv', 'webm', 'm4p', 'mov', 'm4v', 'mpg', '3gp'}
}
if os.path.exists('settings/cache'):
    with open('settings/cache') as file:
        _cache = json.load(file)
    _settings['geometry'] = Geometry(**_cache['geometry']).to_str()
if os.path.exists('settings/config.yaml'):
    with open('settings/config.yaml') as file:
        _config = yaml.safe_load(file)
    _settings['media_extensions'] = _config['media_extensions']
    _settings['paths'] = Paths(**_config['paths'])

CONFIG = Settings(**_settings)


if __name__ == '__main__':
    file_path = 'Family Guy/Season 2/family.guy.s2e10.avi'
    m_file = MediaFile(file_path)
    print(m_file)
    file_path = 'Family Guy/Season 2/family.guy.e11.avi'
    m_file = MediaFile(file_path)
    print(m_file)
    file_path = 'Rush Hour/rush.hour.720p.avi'
    m_file = MediaFile(file_path)
    print(m_file)
