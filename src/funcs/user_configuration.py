import tkinter.filedialog as filedialog
import yaml


def save_paths(settings_path):
    """ Prompts the user to navigate and save the paths to their media.

    Args:
        settings_path (str): The path to the user's config.yaml file

    Returns: The updated users settings
    """
    with open(settings_path) as c:
        settings = yaml.safe_load(c)

    for folder in ['downloads', 'media']:
        path = filedialog.askdirectory(title=f'Choose the path to your {folder.title()} folder.')
        if path:
            settings['paths'][folder] = path

    with open(settings_path, 'w') as n:
        yaml.dump(settings, n, indent=2)

    return settings


def get_user_set_path(settings_path, path='downloads'):
    """ Gets the path to the desired media.
        If the media path is not already settings,
        the user will need to define them.

    Args:
        settings_path (str): The path to the user's config.yaml file
        path (str): The path to retrieve

    Returns: The path
    """
    with open(settings_path) as c:
        settings = yaml.safe_load(c)

    if not settings['paths'].get(path):
        # If the locations are not saved, ask for the locations and save them to a settings file
        settings = save_paths(settings_path, path)

    return settings['paths'][path]



