from importlib import import_module
from .ExtractedArticle import ExtractedArticle
from .WebsiteBase import WebsiteBase
import multiprocessing
import configparser


# **********************************************************************************************************************
def WebsiteFactory(inURL: tuple, inQueue: multiprocessing.Queue, inConfigObject: configparser.ConfigParser) -> WebsiteBase:
    """
    Factory class method to load and return a module that handles the passed-in string
    """

    if not inURL or not inQueue or not inConfigObject:
        return None

    # Instance object to return
    instance = None

    try:
        # Pull the URL and class name from the tuple
        url, classname = inURL

        # Load the module
        classmodule = import_module("." + classname, package="websites")

        tempclass = getattr(classmodule, classname)

        instance = tempclass(inQueue, inConfigObject, url)

        return instance
    except Exception as e:
        raise ImportError("The URL {} cannot be handled at this time.".format(inURL))
