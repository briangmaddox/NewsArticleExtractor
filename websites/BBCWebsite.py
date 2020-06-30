# coding=utf-8

"""
BBCWebsite.py
Describes the class responsible for parsing BBC News articles
"""

import multiprocessing
import configparser
import requests
from bs4 import BeautifulSoup
from .WebsiteBase import WebsiteBase


class BBCWebsite(WebsiteBase):
    """
    This class contains the logic necessary to parse BBC News articles
    """

    # ******************************************************************************************************************
    def __init__(self, inQueue: multiprocessing.Queue, inConfigObject: configparser.ConfigParser, inURL: str):
        """
        Instance constructor
        :param inQueue: input queue to return results
        :param inConfigObject: Configuration object to read from
        """

        # Just pass the input parameters to the base class
        super().__init__(inQueue, inConfigObject, inURL)

    # ******************************************************************************************************************
    def _ParseArticle(self, inURL: str) -> str:
        """
        Method to take the input URL, download the text, strip out the tags, and return the raw text
        :param inURL: URL to download
        :return: string containing the processed text
        """

        try:
            # Get the webpage
            myRequest = requests.get(inURL)

            # Create our BeautifulSoup object
            mySoup = BeautifulSoup(myRequest.content, "lxml")

            # Strip out the tags we don't want
            for tEntity in mySoup(['figure', 'script']):
                tEntity.decompose()

            # Remove Twitter embeds
            for tEntity in mySoup.find_all("div", {'class': 'social-embed'}):
                tEntity.decompose()

            # Remove story-body__link classes
            for tEntity in mySoup.find_all("ul", {'class': 'story-body__unordered-list'}):
                tEntity.decompose()

            # Remove the follow us links
            for tEntity in mySoup.find_all("a", {"class": "story-body__link-external"}):
                tEntity.decompose()

            for tEntity in mySoup.find_all(['script', 'style']):
                tEntity.decompose()

            # grab all the individual paragraphs of the article
            tempArticle = [tEntity.get_text(separator=" ", strip=True) for tEntity in
                           mySoup.find_all('div', {'class': 'story-body__inner'})]

            # Fix some issues that result from BeautifulSoup pulling tags and help Spacy along in general
            returnText = " ".join(tempArticle)
            returnText = self._FixText(returnText)

            # Return the full article text
            return returnText
        except Exception as e:
            print("Exception in BBCWebsite::_ParseArticle: {}".format(e))
            self.good = False
            return str()
