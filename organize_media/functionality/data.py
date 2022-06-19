import os
import json
from PIL import Image, ImageTk
from dataclasses import dataclass, field


@dataclass
class ImageData:
    name: str = ''
    path: str = ''
    width: int = 64
    height: int = 64

    def get(self):
        with Image.open(self.path) as img:
            _image = img.resize((self.width, self.height), Image.ANTIALIAS)
        return ImageTk.PhotoImage(_image)


@dataclass
class Images:
    locate_media: [ImageData] = ImageData('Locate Media', 'Images/dir.png')
    select_media: [ImageData] = ImageData('Select Media', 'Images/filter.png')
    organize: [ImageData] = ImageData('Organize', 'Images/organize_media.png')
    deselect: [ImageData] = ImageData('deselect', 'Images/deselect.png', 24, 24)
    select: [ImageData] = ImageData('select', 'Images/select.png', 24, 24)
    arrow: [ImageData] = ImageData('arrow', 'Images/arrow.png', 24, 24)

    def populate(self):
        self.locate_media = self.locate_media.get()
        self.select_media = self.select_media.get()
        self.organize = self.organize.get()
        self.deselect = self.deselect.get()
        self.select = self.select.get()
        self.arrow = self.arrow.get()


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
