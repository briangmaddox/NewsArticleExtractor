# coding=utf-8

"""
WebsiteBase.py
Describes the base class for all of the derived website classes
"""

from collections import defaultdict
import configparser
import re
import multiprocessing
from typing import List, DefaultDict, Tuple
from urllib.parse import urlparse
import spacy
from fuzzywuzzy import fuzz
import psycopg2
import feedparser
from websites.ExtractedArticle import ExtractedArticle
import re


class WebsiteBase(object):
    """
    This class is the base class for all of the website processing classes.  It defines their interface and provides
    some common functionality for all classes.
    """

    # ******************************************************************************************************************
    def __init__(self, inQueue: multiprocessing.Queue, inConfigObject: configparser.ConfigParser, inURL: str):

        super().__init__()

        # Flag to check if we created OK.
        self.good = True

        # Spacy labels we're interested in
        self._goodLabels = ["PERSON", "FACILITY", "FAC", "ORG", "GPE", "EVENT"]

        # Save the global queue
        if not inQueue:
            self.good = False

            # Don't bother running if we don't have a Queue object passed in
            return

        self._NLP = spacy.load("en_core_web_lg")

        self._queue = inQueue

        # DB Parameters
        self._DBHost = str()
        self._DBPort = str()
        self._DBUser = str()
        self._DBPassword = str()
        self._DBTable = str()

        # DB Objects
        self._DBConnection = None
        self._DBCursor = None

        # Read the configuration
        if not self._ReadConfiguration(inConfigObject):
            self.good = False

            # If we can't read the full configuration, then no need to continue
            return

        # Create the database object and cursor
        if not self._CreateDBObjects():
            self.good = False

            # If we can't create the DB connection, no need to continue
            return

        # Our URL to be set in children
        self._url = inURL

        # Feed items parsed from the RSS link
        self._feedItems = list()

        # Problem entities we need to manually search for
        self._problemEntities = self._GetProblemEntities()

    # ******************************************************************************************************************
    def __del__(self):
        """
        Clean up after ourselves
        :return: None
        """

        try:
            # In case we have any commits outstanding.
            if self._DBConnection:
                self._DBConnection.commit()

            # Now close out
            if self._DBCursor:
                self._DBCursor.close()

            # No need to check here, if it's None the except will catch and ignore
            self._DBConnection.close()
        except Exception as e:
            print("Exception in destructor: {}".format(e))

    # ******************************************************************************************************************
    def _ReadConfiguration(self, inConfigObject: configparser.ConfigParser) -> bool:
        """
        Use the passed-in ConfigParser object to set ourselves up
        :return: True if OK, False otherwise
        """

        try:
            # Get the top level
            DB = inConfigObject["DB"]

            # Now set our member variables
            self._DBHost = DB["DBHost"]
            self._DBPort = DB["DBPort"]
            self._DBUser = DB["DBUser"]
            self._DBPassword = DB["DBPassword"]
            self._DBTable = DB["DBTable"]

            WEBSITEBASEOBJ = inConfigObject["WEBSITEBASE"]

            # Similiarity percentage to go by
            self._fuzzy_ratio = int(WEBSITEBASEOBJ["FuzzyRatio"])

            return True
        except Exception as e:
            print("Got exception {}".format(e))
            self.good = False
            return False

    # ******************************************************************************************************************
    def _CreateDBObjects(self) -> bool:
        """
        Create the psycopg2 object and cursor for the object
        :return: True if successful, False otherwise
        """

        try:
            self._DBConnection = psycopg2.connect(
                    "host={} port={} user={} password={} dbname={}".format(self._DBHost,
                                                                           self._DBPort,
                                                                           self._DBUser,
                                                                           self._DBPassword,
                                                                           self._DBTable))

            if not self._DBConnection:
                self.good = False
                return False

            self._DBCursor = self._DBConnection.cursor()
            if not self._DBCursor:
                self.good = False
                return False

            return True

        except Exception as e:
            self.good = False
            print("Got exception {}".format(e))

    # ******************************************************************************************************************
    def _ResetSQLConnection(self) -> bool:
        """
        Psycopg2 tends to just stop working sometimes on error, so here we reset our connection
        """

        try:
            if self._DBCursor:
                self._DBCursor.close()
            if self._DBConnection:
                self._DBConnection.close()

            self._DBConnection = psycopg2.connect(host=self._DBHost,
                                                  port=self._DBPort,
                                                  dbname=self._DBHost,
                                                  user=self._DBUser,
                                                  password=self._DBPassword)
            self.cursor = self._DBConnection.cursor()
            return True
        except Exception as e:
            print("WebsiteBase::_ResetSQLConnection exception: {}".format(e))
            return False

    # ******************************************************************************************************************
    def _GetFeedItems(self) -> List[ExtractedArticle]:
        """
        Parse the RSS feed for this object.  For each URL in the feed, check if it is already in the DB before adding it
        to the internal to do list.
        :return: List of strings that contain the urls to process
        """

        returnList = list()

        try:
            # First process the RSS feed using feedparser
            print("Using URL: {}".format(self._url))
            myFeedParser = feedparser.parse(self._url)

            # Now for each link, check if it's already in the database before we add it to the return list.
            for entry in myFeedParser.entries:

                # Grab the url
                checkURL = entry.link
                self._DBCursor.execute("SELECT id FROM news_articles WHERE article_url = %s", (checkURL,))
                self._DBConnection.commit()

                if self._DBCursor.fetchone():
                    continue
                else:
                    # Create the wrapper object
                    extractedArticle = ExtractedArticle()

                    extractedArticle.articleTitle = entry.title
                    extractedArticle.articleURL = checkURL
                    extractedArticle.website = urlparse(checkURL).netloc

                    returnList.append(extractedArticle)

            return returnList

        except Exception as e:
            self._ResetSQLConnection()
            self.good = False
            return returnList

    # ******************************************************************************************************************
    def _ParseArticle(self, inURL: str) -> str:
        """
        This method must be overridden in the child classes.  It does the job of scraping the article and returning text
        that can then be passed to Spacy.
        :param inURL: URL to process
        :return: Text output for Spacy
        """
        raise NotImplementedError("Subclass must implement abstract method")

    # ******************************************************************************************************************
    def _CheckSimilarity(self, inText1: str, inText2: str) -> bool:
        """
        Checks the input text for a similarity to the passed-in dictionary
        :param inText1: text string to search
        :param inText2: second string to compare
        :return: bool if the similarity is greater than or equal to the set ration
        """

        # If we didn't get a word passed in, we can't compare so return False
        if not inText1 or not inText2:
            return False

        try:
            ratio = fuzz.partial_ratio(inText1, inText2)

            if ratio >= self._fuzzy_ratio:
                return True

            return False

        except Exception as e:
            print(e)
            return False

    # ******************************************************************************************************************
    def _GetEntities(self, inText: str) -> DefaultDict[str, list]:
        """
        Perform the NLP and create a defaultdict(list) that contains the entities grouped by their spacy type.
        :param inText: text of the article to process
        :return: defaultdict(list) of the extracted entities.
        """

        # Define our return dictionary
        returnDict = defaultdict(list)
        foundIt = False

        # If we didn't get anything passed in, return an empty defaultdict
        if not inText:
            return returnDict

        # Perform the NLP
        tEntities = self._NLP(inText)

        # First check for problem entities
        returnDict = self._ProcessProblemEntities(inText, returnDict)

        # First go through and create the return dictionary
        for tEntity in tEntities.ents:
            foundIt = False
            # Only process if the label is one we are using
            if tEntity.label_ not in self._goodLabels:
                continue

            tText = self._RemoveStopWords(tEntity.text)

            # If we got nothing, don't import
            if not tText:
                continue

            # Don't add if it's in the list of bad expressions
            if self._IsBadEntity(tText):
                continue

            # If the word has already been imported, just continue on
            #if tText in returnDict[tEntity.label_]:
            for tKey, tValues in returnDict.items():
                if tText in tValues:
                    foundIt = True
                    break

            if foundIt:
                continue

            returnDict[tEntity.label_].append(tText.strip())

        # Now we have the entities we are interested in.  We need to do some disambiguation now.
        for label in returnDict:
            for itemCounter in range(len(returnDict[label])):
                # For each list item, we loop through and do a fuzzy comparison with each other item in the same label.
                # If the similarity between the two is high enough, we assume that they are they same.  At that point,
                # we delete the shorter item.
                # TODO: This will likely need to be tweaked at some time in the future.
                for testCounter in range(len(returnDict[label])):
                    if returnDict[label][itemCounter] == returnDict[label][testCounter]:
                        continue

                    # If we have already cleared this out, don't bother checking.
                    if returnDict[label][testCounter] == str() or returnDict[label][itemCounter] == str():
                        continue

                    if self._CheckSimilarity(returnDict[label][itemCounter], returnDict[label][testCounter]):
                        # TODO: This is simplistic....
                        if len(returnDict[label][itemCounter]) < len(returnDict[label][testCounter]):
                            # We set the test entry to an empty string and break out of the testCounter loop
                            returnDict[label][itemCounter] = str()
                            break
                        else:
                            returnDict[label][testCounter] = str()

        # Now go through and clean out the empty strings we used to mark a duplicate
        for label in returnDict:
            returnDict[label] = [x for x in returnDict[label] if x != str()]

        return returnDict

    # ******************************************************************************************************************
    def ProcessFeed(self):
        """
        Grab all of the articles from the RSS feed and process them.
        :return:
        """

        try:
            extractedArticles = self._GetFeedItems()

            # Don't do anything if we have no feeds to process
            if not extractedArticles:
                return

            for article in extractedArticles:
                article.articleText = self._ParseArticle(article.articleURL)

                # If for whatever reason we got no text, continue on
                if not article.articleText:
                    continue

                # Have spacy do the NLP
                nlpEntities = self._GetEntities(article.articleText)

                # Now populate the article
                article.locations.extend(nlpEntities["GPE"])
                article.facilities.extend(nlpEntities["FACILITY"])
                article.facilities.extend(nlpEntities["FAC"])
                article.people.extend(nlpEntities["PERSON"])
                article.organizations.extend(nlpEntities["ORG"])
                article.events.extend(nlpEntities["EVENT"])

                # Now push into the queue
                self._queue.put(article)

        except Exception as e:
            print("Got exception: {}".format(e))

    # ******************************************************************************************************************
    def _RemoveStopWords(self, inText: str) -> str:
        """
        Removes a list of stop words from the input string
        :param inText: input string to strip
        :return: stripped text
        """

        # List of things we want removed
        stopWords = ["the", "a", "mr", "mrs", "ms"]

        # First split up the input string if
        tempWords = inText.split()

        # Do a list comprehension to remove the stopwords
        tempResult = [word for word in tempWords if word.lower() not in stopWords]

        # Return the joined string again
        return ' '.join(tempResult).strip()

    # ******************************************************************************************************************
    def _FixText(self, inText: str) -> str:
        """
        We need to fix some issues that come up from BS4 purging tags and returning the text.  Plus, perform some fixes
        to help Spacy along based on empirical testing.
        :param inText: string
        :return: string
        """

        # Convert "odd" punctuation to "normal"
        tempText = re.sub("’", "'", inText)
        tempText = re.sub("`", "'", tempText)
        tempText = re.sub("“", '"', tempText)
        tempText = re.sub("？", "?", tempText)
        tempText = re.sub("…", " ", tempText)
        # tempText = re.sub("é", "e", tempText)

        # Clean up some of the abbreviations to help with matching partial names with full names later
        tempText = re.sub("\'s", " ", tempText)
        tempText = re.sub("\'ve", " have ", tempText)
        tempText = re.sub("can't", "can not", tempText)
        tempText = re.sub("n't", " not ", tempText)
        tempText = re.sub("i'm", "i am", tempText, flags=re.IGNORECASE)
        tempText = re.sub("\'re", " are ", tempText)
        tempText = re.sub("\'d", " would ", tempText)
        tempText = re.sub("\'ll", " will ", tempText)

        # Fix some end of line issues
        tempText = tempText.replace('."', '. "')
        tempText = tempText.replace("?", "? ")
        # tempText = tempText.replace('."', '. "')
        tempText = tempText.replace('".', '". ')
        tempText = tempText.replace("!", "! ")

        return tempText

    # ******************************************************************************************************************
    def _GetProblemEntities(self) -> List[Tuple]:
        """
        Queries the problem_entities table in the database to get the list of words we need to manually look for
        :return: list(tuple) of values
        """

        try:
            retList = list()

            # Query the database
            self._DBCursor.execute("SELECT entity_name, entity_spacy_label FROM problem_entities")
            self._DBConnection.commit()

            # Get the return values
            values = self._DBCursor.fetchall()

            for entity, spacyLabel in values:
                retList.append((entity, spacyLabel))

            return retList

        except Exception as e:
            print("WebsiteBase::_GetProblemEntities: Exception {}".format(e))
            return list()

    # ******************************************************************************************************************
    def _ProcessProblemEntities(self, inText: str, inDict: DefaultDict[str, List]) -> DefaultDict[str, List]:
        """
        Check for entities that Spacy has trouble with and manually append them to the list if necessary
        :param inDict: DefaultDict[List] of found entities
        :return: DefaultDict[List] of modified entities
        """

        try:
            for entity, label in self._problemEntities:
                if entity in inText:
                    inDict[label].append(entity)

            return inDict

        except Exception as e:
            print("WebsiteBase::_ProcessProblemEntities: Exception: {}".format(e))
            return inDict

    # ******************************************************************************************************************
    def _IsBadEntity(self, inEntity: str) -> bool:
        """
        Checks if the entity is in a list of bad entities found in processing
        :param inEntity: string to check
        :return: True if found, False otherwise
        """

        try:
            if re.match(r"\d+\S", inEntity):
                return True

            if re.match(r"^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", inEntity):
                return True

            return False
        except Exception as e:
            print("WebsiteBase::_IsBadEntity: Exception: {}".format(e))
            return False
