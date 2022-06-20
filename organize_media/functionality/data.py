import os
import json
from PIL import Image, ImageTk
from dataclasses import dataclass


class OMImage(ImageTk.PhotoImage):
    """
        Extends the functionality of ImageTk.PhotoImage.
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


@dataclass
class Geometry:
    w: int = 1000
    h: int = 800
    x: int = 0
    y: int = 0


@dataclass
class Colors:
    main: str = '#141414'
    sub: str = '#232323'
    special: str = '#5c0f80'
    special_alt: str = '#b435f0'
    alt: str = '#3c6fc2'
    font: str = '#ffffff'


@dataclass
class Fonts:
    xxsmall: tuple = ('Constantia', 11)
    xsmall: tuple = ('Constantia', 12)
    small: tuple = ('Constantia', 13)
    medium: tuple = ('Constantia', 14)
    large: tuple = ('Constantia', 18)
    xlarge: tuple = ('Constantia', 22)
    xxlarge: tuple = ('Constantia', 40)


@dataclass
class Settings:
    title: str = 'Media Organizer'
    geometry: [Geometry] = Geometry()
    colors: [Colors] = Colors()
    fonts: [Fonts] = Fonts()


# Set the Settings
if os.path.exists('settings/cache'):
    with open('settings/cache') as file:
        cache = json.load(file)
    CONFIG = Settings(geometry=Geometry(**cache['geometry']))
else:
    CONFIG = Settings()

user_settings_template = {
    'media_extensions': ['mp4', 'mkv', 'avi', 'flv', 'wmv', 'webm', 'm4p', 'mov', 'm4v', 'mpg', '3gp'],
    'paths': {
        'downloads': '',
        'media': ''
    }
}

if __name__ == '__main__':
    print(CONFIG.colors.main)
