# organize-media
A Python GUI tool, used for organizing your local media files.

## Installation
- Download the `Organize Media` folder, and run from  there.
- The application is light-weight, meaning it will run from wherever the app folder is saved.

## Compile
To compile the application, run the following:
```
pip install pyinstaller
pyinstaller -w -F --paths organize_media --paths organize_media/functionality --distpath "./Organize Media" -n "Organize Media" organize_media/organize_media.py
```