# coding=utf-8

"""
newsextractor.py
Main driver program that creates the queue and subprocesses
"""

from configparser import ConfigParser
import multiprocessing
import os
import sys
from typing import List
import time
import psycopg2
import websites
from DBWriter import DBWriter


# **********************************************************************************************************************
def GetSubscriptions(inConfigObject: ConfigParser) -> List:
    """
    Gets the list of subscripts from the database
    :return: List of tuples
    """

    try:
        returnList = list()

        # Get the top level
        DB = inConfigObject["DB"]

        # Now set our member variables
        DBHost = DB["DBHost"]
        DBPort = DB["DBPort"]
        DBUser = DB["DBUser"]
        DBPassword = DB["DBPassword"]
        DBTable = DB["DBTable"]

        DBCOnnection = psycopg2.connect(host=DBHost,
                                         port=DBPort,
                                         dbname=DBTable,
                                         user=DBUser,
                                         password=DBPassword)
        cursor = DBCOnnection.cursor()

        cursor.execute("SELECT url, classname FROM subscriptions;")
        DBCOnnection.commit()

        returnList = cursor.fetchall()

        # clean up
        cursor.close()
        DBCOnnection.close()

        return returnList

    except Exception as gsException:
        print("Exception in newsextractor::GetSubscriptions: {}".format(gsException))
        return list()


# **********************************************************************************************************************
def AddPoisonPill():
    """
    Adds the poison pill to the queue so we shut down gracefully
    :return: Nothing
    """

    try:
        # Shut down the dbwriter
        killArticle = websites.ExtractedArticle()

        # Create the poison pill
        killArticle.articleText = "EXITCALLED"

        # Place the poison pill on the queue
        articleQueue.put(killArticle)

        return
    except Exception as e:
        print("newsextractor: Exception in AddPoisonPill: {}".format(e))
        return


# **********************************************************************************************************************
if __name__ == '__main__':
    try:
        localtime = time.asctime(time.localtime(time.time()))
        print("Local current time :", localtime)

        # Create our queue object
        articleQueue = multiprocessing.Queue()

        # Create our configuration object
        # Get the base directory for this file
        plugin_path = os.path.dirname(os.path.realpath(__file__))

        # Now create the object and read in the config.ini
        configObject = ConfigParser()
        configObject.read(plugin_path + "/config.ini")

        # Get the list of subscriptions and their objects that we need to process
        urlList = GetSubscriptions(configObject)

        # If we do not have a list of URLS to process, just exit
        if not urlList:
            print("newsextractor: No list of subscriptions.  Exiting...")
            sys.exit(-1)

        # Create and start the DB Writer
        dbWriter = DBWriter(articleQueue, configObject)
        dbWriter.start()

        # Start processing
        for url in urlList:
            websiteObject = websites.WebsiteFactory(url, articleQueue, configObject)
            websiteObject.ProcessFeed()

        AddPoisonPill()

        dbWriter.join()

        localtime = time.asctime(time.localtime(time.time()))
        print("Local current time :", localtime)

        print("Exiting...")

    except Exception as e:
        print("Exception in newsextractor main: {}".format(e))
        sys.exit(-1)
