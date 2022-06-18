# organize-media
A Python GUI tool, used for organizing your local media files.

## Installation
- [Download the Organize Media folder](https://downgit.github.io/#/home?url=https://github.com/JustinGrilli/organize-media/tree/main/Organize%20Media)
  - Currently only supported on Windows. (v10+)
  - The program will run from wherever the `Organize Media` folder is saved.
  - It does not need to be installed after it has been downloaded.

## Compile
To compile the application, run the following:
```
pip install pyinstaller
pyinstaller -w -F --paths organize_media --paths organize_media/functionality --distpath "./Organize Media" -n "Organize Media" organize_media/organize_media.py
```