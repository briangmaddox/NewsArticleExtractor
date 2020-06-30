# coding=utf-8

"""
ExtractedArticle.py
Describes the class that holds article information
"""


class ExtractedArticle(object):
    """
     This class holds all of the information that was pulled from the article.  It is
     passed to the DB thread to extract and push to the database.
    """

    # ******************************************************************************************************************
    def __init__(self):
        # Basic information
        self.articleTitle = str()  # Holds the title of the article.
        self.articleText = str()  # Holds the cleaned up full text of the article.
        self.articleURL = str()  # URL for the article.
        self.website = str()  # Website that the article is under (i.e., www.bbc.com).

        # Extracted information
        self.locations = list()  # List of locations pulled from the article.
        self.facilities = list()  # List of facilities extracted from the text.
        self.people = list()  # List of people extracted from the article.
        self.organizations = list()  # List of organizations extracted from the article.
        self.events = list()  # List of events extracted from the article.
