# coding=utf-8

"""
DBWriter.py
Describes the class that runs as a separate process and writes data to the database as it is pushed into a global queue.
"""

import multiprocessing
import configparser
import psycopg2
from typing import List, Tuple
from websites import ExtractedArticle
from psycopg2 import sql


class DBWriter(multiprocessing.Process):
    """
    This class is responsible for checking the global queue for objects.  If any have been placed, it will then write
    them to the database.  It runs in it's own process.
    """

    # ******************************************************************************************************************
    def __init__(self, inQueue: multiprocessing.Queue, inConfigObject: configparser.ConfigParser):
        """
        Perform our specific setup
        :param inQueue: multiprocessing.Queue object to read from
        """

        try:
            multiprocessing.Process.__init__(self, group=None)

            # Flag to check if we created OK.
            self.good = True

            # Save the global queue
            if not inQueue:
                self.good = False

                # Don't bother running if we don't have a Queue object passed in
                return

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

        except Exception as e:
            print("Exception in DBWriter::__init__: {}".format(e))
            self.good = False

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
            print("Exception in DBWriter::__del__: {}".format(e))

    # ******************************************************************************************************************
    def _ResetSQLConnection(self) -> bool:
        """
        Psycopg2 tends to just stop working sometimes on error, so here we just reset our connection
        """

        try:
            if self._DBCursor:
                self._DBCursor.close()
            if self._DBConnection:
                self._DBConnection.close()

            self._DBConnection = psycopg2.connect(host=self._DBHost,
                                                  port=self._DBPort,
                                                  dbname=self._DBTable,
                                                  user=self._DBUser,
                                                  password=self._DBPassword)
            self._DBCursor = self._DBConnection.cursor()

            return True

        except Exception as e:
            print("Exception in DBWriter::_ResetSQLConnection: {}".format(e))
            return False

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

            return True

        except Exception as e:
            print("Exception in DBWriter::_ReadConfiguration: {}".format(e))
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
            print("Exception in DBWriter::_CreateDBObjects: {}".format(e))
            return False

    # ******************************************************************************************************************
    def _InsertArticlePeople(self, inArticleID: int, inPeopleID: int):
        """
        Insert the passed-in values to the database.
        :param inArticleID: integer article identifier
        :param inPeopleID: integer person identifier
        :return: none
        """

        try:
            # Do not do anything if nothing passed in
            if not inArticleID or not inPeopleID:
                return

            # Don't do anything if we are debugging
            if inArticleID == -1:
                return

            print("INSERT INTO article_people (article_id, people_id) VALUES ({}, {});".format(inArticleID, inPeopleID))
            self._DBCursor.execute("INSERT INTO article_people (article_id, people_id) VALUES (%s, %s);",
                                   (inArticleID, inPeopleID))
            self._DBConnection.commit()

        except Exception as e:
            print("Exception in DBWriter::_InsertArticlePeople: {}".format(e))
            self._ResetSQLConnection()

    # ******************************************************************************************************************
    def _InsertArticleLocations(self, inArticleID: int, inLocationID: int):
        """
        Insert the passed-in values to the database.
        :param inArticleID: integer article identifier
        :param inLocationID: integer location identifier
        :return: none
        """

        try:
            # Do not do anything if nothing passed in
            if not inArticleID or not inLocationID:
                return

            # Don't do anything if we are debugging
            if inArticleID == -1:
                return

            print("INSERT INTO article_locations (article_id, location_id) VALUES ({}, {});".format(inArticleID,
                                                                                                    inLocationID))
            self._DBCursor.execute("INSERT INTO article_locations (article_id, location_id) VALUES (%s, %s);",
                                   (inArticleID, inLocationID))
            self._DBConnection.commit()

        except Exception as e:
            print("Exception in DBWriter::_InsertArticleLocations: {}".format(e))
            self._ResetSQLConnection()

    # ******************************************************************************************************************
    def _InsertArticleFacilities(self, inArticleID: int, inFacilityID: int):
        """
        Insert the passed-in values to the database.
        :param inArticleID: integer article identifier
        :param inFacilityID: integer facility identifier
        :return: none
        """

        try:
            # Do not do anything if nothing passed in
            if not inArticleID or not inFacilityID:
                return

            # Don't do anything if we are debugging
            if inArticleID == -1:
                return

            print("INSERT INTO article_facilities (article_id, facility_id) VALUES ({}, {});".format(inArticleID,
                                                                                                     inFacilityID))
            self._DBCursor.execute("INSERT INTO article_facilities (article_id, facility_id) VALUES (%s, %s);",
                                   (inArticleID, inFacilityID))
            self._DBConnection.commit()

        except Exception as e:
            print("Exception in DBWriter::_InsertArticleFacilities: {}".format(e))
            self._ResetSQLConnection()

    # ******************************************************************************************************************
    def _InsertArticleOrganizations(self, inArticleID: int, inOrganizationID: int):
        """
        Insert the passed-in values to the database.
        :param inArticleID: integer article identifier
        :param inOrganizationID: integer organization identifier
        :return: none
        """

        try:
            # Do not do anything if nothing passed in
            if not inArticleID or not inOrganizationID:
                return

            # Don't do anything if we are debugging
            if inArticleID == -1:
                return

            print("INSERT INTO article_organizations (article_id, organization_id) VALUES ({}, {});".format(inArticleID,
                                                                                                            inOrganizationID))
            self._DBCursor.execute("INSERT INTO article_organizations (article_id, organization_Id) VALUES (%s, %s);",
                                   (inArticleID, inOrganizationID))
            self._DBConnection.commit()

        except Exception as e:
            print("Exception in DBWriter::_InsertArticleOrganizations: {}".format(e))
            self._ResetSQLConnection()

    # ******************************************************************************************************************
    def _InsertArticleEvents(self, inArticleID: int, inEventID: int):
        """
        Insert the passed-in values to the database.
        :param inArticleID: integer article identifier
        :param inEventID: integer event identifier
        :return: none
        """

        try:
            # Do not do anything if nothing passed in
            if not inArticleID or not inEventID:
                return

            # Don't do anything if we are debugging
            if inArticleID == -1:
                return

            print("INSERT INTO article_events (article_id, event_id) VALUES ({}, {});".format(inArticleID, inEventID))
            self._DBCursor.execute("INSERT INTO article_events (article_id, event_id) VALUES (%s, %s);",
                                   (inArticleID, inEventID))
            self._DBConnection.commit()

        except Exception as e:
            print("Exception in DBWriter::_InsertArticleEvents: {}".format(e))
            self._ResetSQLConnection()

    # ******************************************************************************************************************
    def _InsertPerson(self, inPersonName: str) -> int:
        """
        Inserts a person into the database and returns the value of the inserted name
        :param inPersonName: string to insert
        :return: integer representing the id of the added person, -1 on error
        """

        try:
            if not inPersonName:
                return -1

            print("INSERT INTO people (name) VALUES ({}) RETURNING id;".format(inPersonName))
            self._DBCursor.execute("INSERT INTO people (name) VALUES (%s) RETURNING id;", (inPersonName,))
            self._DBConnection.commit()

            result = self._DBCursor.fetchone()
            if result:
                return result[0]
            else:
                return -1

        except Exception as e:
            print("Exception in DBWriter::_InsertPerson: {}".format(e))
            self._ResetSQLConnection()
            return -1

    # ******************************************************************************************************************
    def _InsertLocation(self, inLocationName: str) -> int:
        """
        Inserts a location into the database and returns the value of the inserted name
        :param inLocationName: string to insert
        :return: integer representing the id of the added location, -1 on error
        """

        try:
            if not inLocationName:
                return -1

            print("INSERT INTO locations (name) VALUES ({}) RETURNING id;".format(inLocationName))
            self._DBCursor.execute("INSERT INTO locations (name) VALUES (%s) RETURNING id;", (inLocationName,))
            self._DBConnection.commit()

            result = self._DBCursor.fetchone()
            if result:
                return result[0]
            else:
                return -1

        except Exception as e:
            print("Exception in DBWriter::_InsertLocation: {}".format(e))
            self._ResetSQLConnection()
            return -1

    # ******************************************************************************************************************
    def _InsertFacility(self, inFacilityName: str) -> int:
        """
        Inserts a location into the database and returns the value of the inserted name
        :param inFacilityName: string to insert
        :return: integer representing the id of the added facility, -1 on error
        """

        try:
            if not inFacilityName:
                return -1

            print("INSERT INTO facilities (name) VALUES ({}) RETURNING id;".format(inFacilityName))
            self._DBCursor.execute("INSERT INTO facilities (name) VALUES (%s) RETURNING id;", (inFacilityName,))
            self._DBConnection.commit()

            result = self._DBCursor.fetchone()
            if result:
                return result[0]
            else:
                return -1

        except Exception as e:
            print("Exception in DBWriter::_InsertFacility: {}".format(e))
            self._ResetSQLConnection()
            return -1

    # ******************************************************************************************************************
    def _InsertOrganization(self, inOrganizationName: str) -> int:
        """
        Inserts a location into the database and returns the value of the inserted name
        :param inOrganizationName: string to insert
        :return: integer representing the id of the added organization, -1 on error
        """

        try:
            if not inOrganizationName:
                return -1

            print("INSERT INTO organizations (name) VALUES ({}) RETURNING id;".format(inOrganizationName))
            self._DBCursor.execute("INSERT INTO organizations (name) VALUES (%s) RETURNING id;",
                                   (inOrganizationName,))
            self._DBConnection.commit()

            result = self._DBCursor.fetchone()
            if result:
                return result[0]
            else:
                return -1

        except Exception as e:
            print("Exception in DBWriter::_InsertOrganization: {}".format(e))
            self._ResetSQLConnection()
            return -1

    # ******************************************************************************************************************
    def _InsertEvent(self, inEventName: str) -> int:
        """
        Inserts a location into the database and returns the value of the inserted name
        :param inEventName: string to insert
        :return: integer representing the id of the added event, -1 on error
        """

        try:
            if not inEventName:
                return -1

            print("INSERT INTO event (name) VALUES ({}) RETURNING id;".format(inEventName))
            self._DBCursor.execute("INSERT INTO event (name) VALUES (%s) RETURNING id;", (inEventName,))
            self._DBConnection.commit()

            result = self._DBCursor.fetchone()
            if result:
                return result[0]
            else:
                return -1

        except Exception as e:
            print("Exception in DBWriter::_InsertEvent: {}".format(e))
            self._ResetSQLConnection()
            return -1

    # ******************************************************************************************************************
    def _ProcessPeople(self, inArticleID: int, inPeopleList: list):
        """
        Takes the input list of people and article id.  Searches the DB for a match for the person name. If found, add
        an entry to the ArticlesPeople otherwise add a new person and then add the entry.
        :param inArticleID: Integer identifier of the added article
        :param inPeopleList: list of people to link to the article
        :return:
        """

        try:
            for person in inPeopleList:
                personID = self._GetUniqueCommon(person, "people")

                if personID != -1:
                    self._InsertArticlePeople(inArticleID, personID)
                else:
                    # We could not (reliably) find a single match in the DB.  Add the person and then the
                    # article link.
                    personID = self._InsertPerson(person)
                    if personID != -1:
                        self._InsertArticlePeople(inArticleID, personID)

        except Exception as e:
            print("Exception in DBWriter::_ProcessPeople: {}".format(e))
            self._ResetSQLConnection()

    # ******************************************************************************************************************
    def _ProcessLocations(self, inArticleID: int, inLocationList: list):
        """
        Takes the input list of locations and article id.  Searches the DB for a match for the location name. If found,
        add an entry to the ArticlesLocations, otherwise add a new location and then add the entry.
        :param inArticleID: Integer identifier of the added article
        :param inLocationList: list of locations to link to the article
        :return:
        """

        # FIXME This needs to be modified to do a better job finding locations (ie, finish searching for other fields logic, etc.

        adminList = None

        print("Locations: *****************************")
        print(inLocationList)

        try:
            for location in inLocationList:
                # Run location disambiguation case 1 (check for a unique location result)
                locationID = self._GetUniqueCommon(location, "locations")
                if locationID != -1:
                    self._InsertArticleLocations(inArticleID, locationID)
                    continue

                # For Case 2, we first get check the list of locations to see if any of them are countries or states
                # If so, we check the other locations to see if they are in the list of countries that we got back.
                # Populate adminList if we haven't already
                if not adminList:
                    adminList = self._FindCountries(inLocationList)

                # If we handled it here, move to the next location
                if self._LocationCaseTwo(inArticleID, location, adminList):
                    continue

                # Are there multiple exact name matches?  If so pick the one with the highest population
                if self._LocationCaseThree(inArticleID, location):
                    continue

                # So if we get here, we could not (reliably) find a single match in the DB.  Add the location and then
                # the article link.
                locationID = self._InsertLocation(location)
                if locationID != -1:
                    self._InsertArticleLocations(inArticleID, locationID)

        except Exception as e:
            print("Exception in DBWriter::_ProcessLocations: {}".format(e))
            self._ResetSQLConnection()

    # ******************************************************************************************************************
    def _ProcessFacilities(self, inArticleID: int, inFacilityList: list):
        """
        Takes the input list of facilities and article id.  Searches the DB for a match for the facility name. If found,
        add an entry to the ArticlesFacilities, otherwise add a new facility and then add the entry.
        :param inArticleID: Integer identifier of the added article
        :param inFacilityList: list of facilities to link to the article
        :return:
        """

        try:
            for facility in inFacilityList:
                facilityID = self._GetUniqueCommon(facility, "facilities")

                if facilityID != -1:
                    self._InsertArticleFacilities(inArticleID, facilityID)
                else:
                    # We could not (reliably) find a single match in the DB.  Add the person and then the
                    # article link.
                    facilityID = self._InsertFacility(facility)
                    if facilityID != -1:
                        self._InsertArticleFacilities(inArticleID, facilityID)

        except Exception as e:
            print("Exception in DBWriter::_ProcessFacilities: {}".format(e))
            self._ResetSQLConnection()

    # ******************************************************************************************************************
    def _ProcessOrganizations(self, inArticleID: int, inOrganizationList: list):
        """
        Takes the input list of organizations and article id.  Searches the DB for a match for the organization name.
        If found, add an entry to the ArticlesOrganizations, otherwise add a new organization and then add the entry.
        :param inArticleID: Integer identifier of the added article
        :param inOrganizationList: list of organizations to link to the article
        :return:
        """

        try:
            for organization in inOrganizationList:
                organizationID = self._GetUniqueCommon(organization, "organizations")

                if organizationID != -1:
                    self._InsertArticleOrganizations(inArticleID, organizationID)
                else:
                    # We could not (reliably) find a single match in the DB.  Add the person and then the
                    # article link.
                    organizationID = self._InsertOrganization(organization)
                    if organizationID != -1:
                        self._InsertArticleOrganizations(inArticleID, organizationID)

        except Exception as e:
            print("Exception in DBWriter::_ProcessOrganizations: {}".format(e))
            self._ResetSQLConnection()

    # ******************************************************************************************************************
    def _ProcessEvents(self, inArticleID: int, inEventList: list):
        """
        Takes the input list of events and article id.  Searches the DB for a match for the event name.
        If found, add an entry to the ArticlesEvents, otherwise add a new event and then add the entry.
        :param inArticleID: Integer identifier of the added article
        :param inEventList: list of events to link to the article
        :return:
        """

        try:
            for event in inEventList:
                eventID = self._GetUniqueCommon(event, "event")

                if eventID != -1:
                    self._InsertArticleEvents(inArticleID, eventID)
                else:
                    # We could not (reliably) find a single match in the DB.  Add the person and then the
                    # article link.
                    eventID = self._InsertEvent(event)
                    if eventID != -1:
                        self._InsertArticleEvents(inArticleID, eventID)

        except Exception as e:
            print("Exception in DBWriter::_ProcessEvents: {}".format(e))
            self._ResetSQLConnection()

    # ******************************************************************************************************************
    def WriteEntries(self, inArticleObject: ExtractedArticle):
        """
        This is the main part of the thread that pulls from the global queue and then writes it into the database
        :return:
        """

        try:
            # Push the article metadata to the DB and get the assigned identifier for it.
            print("""
                 INSERT INTO news_articles (article_title, article_url, article_text, website)
                 VALUES ({}, {}, {}, {}) RETURNING id;
                 """.format(inArticleObject.articleTitle, inArticleObject.articleURL, inArticleObject.articleText,
                            inArticleObject.website))
            self._DBCursor.execute("""
                                    INSERT INTO news_articles (article_title, article_url, article_text, website)
                                    VALUES (%s, %s, %s, %s) RETURNING id;
                                    """,
                                   (inArticleObject.articleTitle, inArticleObject.articleURL,
                                     inArticleObject.articleText, inArticleObject.website))
            self._DBConnection.commit()

            # Get the ID of the inserted object
            articleID = self._DBCursor.fetchone()[0]

            # Now populate the article_people table
            self._ProcessPeople(articleID, inArticleObject.people)

            # Now populate the article_facilities table
            self._ProcessFacilities(articleID, inArticleObject.facilities)

            # Now populate the article_organizations table
            self._ProcessOrganizations(articleID, inArticleObject.organizations)

            # Now populate the article_events table
            self._ProcessEvents(articleID, inArticleObject.events)

            # Now populate the article_locations table
            self._ProcessLocations(articleID, inArticleObject.locations)

        except Exception as e:
            print("Exception in DBWriter::WriteEntries: {}".format(e))
            self.good = False
            self._ResetSQLConnection()

    # ******************************************************************************************************************
    def run(self):
        """
        Override to handle the main loop of the process
        :return:
        """

        continueFlag = True

        while continueFlag:
            articleObject = self._queue.get()

            # Check for our poison pill
            if articleObject.articleText == "EXITCALLED":
                continueFlag = False
                continue

            self.WriteEntries(articleObject)

    # ******************************************************************************************************************
    def _LocationCaseTwo(self, inArticleID: int, inLocation: str, inAdminList: List[Tuple]) -> bool:
        """
        Check to see if any of the locations are in any of the administrative areas in adminList.  We commit IFF we get
        a single match for any of the locations.
        :param inArticleID: ID of the article we're processing
        :param inLocation: Input location string to check
        :param inAdminList: list of tuples with administative names and their CC2 codes.
        :return: True if we wrote the entry to the database
        """

        if not inAdminList or not inLocation:
            return False

        try:
            for tempAdmin in inAdminList:
                # FIXME: Skip for now if it's a country, may want to add it in the future.
                # if inLocation in dict(inAdminList):
                #    continue

                # First check if we get a single match for the location vs the country.
                self._DBCursor.execute("SELECT id FROM locations WHERE name = %s AND cc2 = %s;",
                                       (inLocation, tempAdmin[1]))
                self._DBConnection.commit()

                if self._DBCursor.rowcount == 1:
                    locationID = self._DBCursor.fetchone()
                    self._InsertArticleLocations(inArticleID, locationID[0])
                    return True
                elif self._DBCursor.rowcount > 1:
                    # Pick the match with the highest population.
                    self._DBCursor.execute("""
                                            SELECT id, population FROM locations WHERE name = %s AND cc2 = %s AND
                                            population IS NOT NULL ORDER BY population DESC LIMIT 1;
                                            """, (inLocation, tempAdmin[1]))
                    self._DBConnection.commit()
                    locationID = self._DBCursor.fetchone()
                    self._InsertArticleLocations(inArticleID, locationID[0])
                    return True

                # Second, check for a similarity score but we only use it if we get a single result.
                self._DBCursor.execute("""
                                        SELECT id FROM locations WHERE SIMILARITY(name, %s) > 0.5 AND cc2 = %s;
                                        """, (inLocation, tempAdmin[1]))
                self._DBConnection.commit()
                if self._DBCursor.rowcount == 1:
                    locationID = self._DBCursor.fetchone()
                    self._InsertArticleLocations(inArticleID, locationID[0])
                    return True

                # Check aliases
                # Second check: Look in the aliases column
                nameString = inLocation.replace("'", "''").replace('"', '\\"')
                sqlString = "SELECT id FROM locations WHERE aliases @> '{%s}'" % nameString
                sqlString = sqlString + " AND cc2 = %s;"
                self._DBCursor.execute(sqlString, (tempAdmin[1],))
                self._DBConnection.commit()

                if self._DBCursor.rowcount == 1:
                    # Only add if we got a single result (since there are cases of multiple Northern Provinces, etc
                    locationID = self._DBCursor.fetchone()

                    if locationID:
                        self._InsertArticleLocations(inArticleID, locationID[0])
                        return True

        except Exception as e:
            print("DBWriter::_LocationCaseTwo Exception: {}".format(e))
            self._ResetSQLConnection()
            return False

        # If we got here, we didn't find a perfect match.
        return False

    # ******************************************************************************************************************
    def _LocationCaseThree(self, inArticleID: int, inLocation: str) -> bool:
        """
        Perform a search.  If we get multiple name matches, pick the one with the highest population.
        :param inArticleID: ID of the article we're processing
        :param inLocation: Input location string to check
        :return: True if we wrote the entry to the database
        """

        if not inArticleID or not inLocation:
            return False

        try:
            self._DBCursor.execute("""
                                    SELECT id, population FROM locations WHERE name = %s AND
                                    population IS NOT NULL ORDER BY population DESC;
                                    """, (inLocation, ))
            self._DBConnection.commit()
            if self._DBCursor.rowcount > 1:
                locationID = self._DBCursor.fetchone()
                self._InsertArticleLocations(inArticleID, locationID[0])
                return True

        except Exception as e:
            print("DBWriter::_LocationCaseThree Exception: {}".format(e))
            self._ResetSQLConnection()
            return False

        # If we got here, we didn't find any matches.
        return False

    # ******************************************************************************************************************
    def _FindCountries(self, inLocations: list) -> List[Tuple]:
        """
        Check the input list and return a new list if the name in the list is in the locations db with a fclasscode of
        A.ADM1
        :param inLocations: list of location names to check
        :return: list of locations that are countries or states
        """

        returnList = list()

        try:
            for location in inLocations:
                # First, Is it an exact name match?
                self._DBCursor.execute("SELECT name, cc2 from countries where name = %s;", (location,))
                self._DBConnection.commit()

                if self._DBCursor.rowcount == 1:
                    # Only add if we got a single result (since there are cases of multiple Northern Provinces, etc
                    locationID = self._DBCursor.fetchone()

                    if locationID:
                        returnList.append((locationID[0], locationID[1]))
                        continue

                # Second check: Look in the aliases column
                nameString = location.replace("'", "''").replace('"', '\\"')
                sqlString = "SELECT name, cc2 FROM countries WHERE aliases @> '{%s}';" % nameString
                self._DBCursor.execute(sqlString)
                self._DBConnection.commit()

                if self._DBCursor.rowcount == 1:
                    # Only add if we got a single result (since there are cases of multiple Northern Provinces, etc
                    locationID = self._DBCursor.fetchone()

                    if locationID:
                        returnList.append((locationID[0], locationID[1]))
                        continue

                # Third check: Look for a single row that has a similarity > 0.5 (IFF there was a single result)
                self._DBCursor.execute("SELECT name, cc2 FROM countries WHERE SIMILARITY(name, %s) > 0.5;",
                                       (location,))
                self._DBConnection.commit()

                if self._DBCursor.rowcount == 1:
                    locationID = self._DBCursor.fetchone()

                    if locationID:
                        returnList.append((locationID[0], locationID[1]))
                        continue

                # Fourth check.  Check similarity in the aliases column.
                self._DBCursor.execute("""
                                        SELECT name, cc2 FROM countries, UNNEST(countries.aliases) p 
                                        WHERE SIMILARITY(p, %s) > 0.5;
                                        """, (location,))
                self._DBConnection.commit()

                if self._DBCursor.rowcount == 1:
                    locationID = self._DBCursor.fetchone()

                    if locationID:
                        returnList.append((locationID[0], locationID[1]))
                        continue

        except Exception as e:
            print("Got exception in DBWriter::_FindCountries: {}".format(e))
            return list()

        return returnList

    # ******************************************************************************************************************
    def _GetUniqueCommon(self, inName: str, inTable: str) -> int:
        """
        This logic was broken out as several functions use it as part of trying to find a match for an input name, be it
        person, places, or things.
        :param inName: Input name to search for
        :param inTable: Input table name for the query
        :return: ID of the found name, -1 otherwise
        """

        try:
            # First check for exact matches
            self._DBCursor.execute(sql.SQL("SELECT id FROM {} WHERE name = %s;").format(sql.Identifier(inTable)),
                                   (inName,))
            self._DBConnection.commit()

            # We got a single result on the location from the Locations DB so just use it.
            if self._DBCursor.rowcount == 1:
                locationID = self._DBCursor.fetchone()

                if locationID:
                    return int(locationID[0])

            # Second check: look in the aliases column for an exact match unless it's locations
            # Create the SQL string.  We're trying to shoehorn a string here so need to do it twice because psycopg2
            # sql module does not like having @> in a string.
            nameString = inName.replace("'", "''").replace('"', '\\"')
            sqlString = "SELECT id FROM {} ".format(inTable)
            sqlString = sqlString + "WHERE aliases @> '{%s}';" % nameString
            self._DBCursor.execute(sqlString)
            self._DBConnection.commit()

            if self._DBCursor.rowcount == 1:
                locationID = self._DBCursor.fetchone()

                if locationID:
                    return int(locationID[0])

            # Third check: Look for a single row that has a similarity > 0.5 (IFF there was a single result)
            self._DBCursor.execute(sql.SQL("SELECT id FROM {} WHERE SIMILARITY(name, %s) > 0.5;").
                                   format(sql.Identifier(inTable)), (inName, ))
            self._DBConnection.commit()

            if self._DBCursor.rowcount == 1:
                locationID = self._DBCursor.fetchone()

                if locationID:
                    return int(locationID[0])

            #if inTable != "locations":
            # Fourth check: Look for a match in aliases with a similarity() > 0.5 (IFF there was a single result)
            self._DBCursor.execute(sql.SQL(
                                    """
                                    SELECT id FROM {}, UNNEST({}.aliases) p WHERE SIMILARITY(p, %s) > 0.5;
                                    """).format(sql.Identifier(inTable), sql.Identifier(inTable)), (inName,))
            self._DBConnection.commit()

            if self._DBCursor.rowcount == 1:
                locationID = self._DBCursor.fetchone()

                if locationID:
                    return int(locationID[0])
        except Exception as e:
            print("Exception in DBWriter::_GetUniqueCommon: {}".format(e))
            return -1

        # if we made it here we didn't find anything
        return -1
