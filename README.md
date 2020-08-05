# News Article Extractor
Website news article scraper and geospatial enabler

THIS IS A WORK IN PROGRESS!!!  It's a side research project of mine.  
Currently it only works with English webpages.

Am moving from my personal repository to Github.

## Getting Started
This application uses PostgreSQL with the PostGIS extensions installed.

### Prerequisites
You should create a Python 3 virtual environment for this and then install the requirements with the provided requirements.txt
```
pip install -r requirements.txt
```

Next, you should restore the file newsarticles_schema.dump after you have created  a PostgreSQL database and enabled PostGIS. 

```
cat newsarticles_schema.dump |psql -d YOURDBNAME
```
or
```
pg_restore -d YOURDBNAME newsarticles_schema.dump
```

This assumes you have the Spacy English large model installed.
```
python -m spacy download en_core_web_lg
```
There is an ER diagram under Documentation called **news_articles_er_diagram.png**.

Next, you can load a Geonames extract into the locations table if you like.  See my repository _misc_gis_scripts_ at 
https://github.com/briangmaddox/misc_gis_scripts for an example how to do this.

After that, I have provided some csv files in the **SQL** directory to load.  The **problem_entities.csv** file is for entries that I found had problems with Spacy.
**subscriptions.csv** contains an example subscription entry.  **countries.csv** contains a list of countries and some aliases that I have come across while working on this.

Finally, modify the file config.ini with your database parameters.

## Running
The application is designed to be run manually or via a cron job.

The control flow is:
* Download the RSS file from the website.
* For each article in the feed, check which articles are new and process those.
* Use BeautifulSoup4 to scrape the webpage.
* Run the text through Spacy to perform NLP.
* Attempt to find and geolocate any locations mentioned in the article.
* Store the entries in the database.

The basic idea is to add an entry in the subscriptions table that contains a URL, a name, and a class name.
Next, implement the class under Websites that implements the processing for that website and derives from WebsiteBase.py.

At runtime, the program will pull the subscriptions list from the database and go through the entries there, using the WebsiteFactory function to dynamically load the
class name specified in the database.  After some time it will run and store the results in the database.

If you run into entries that seem to always get mis-categorized by Spacy, add them to the **problem_entities** table.  See the examples in the above-mentioned csv.

Depending on how often this runs, it can take a while to process the RSS feed of a website.

### New entries and Maintenance
In general, if it does not find an existing entry in the **event**, **facilities**, **locations**, **organizations**, or **people** tables, this will
add them to the respective tables.  You should monitor these tables to periodically add in any missing information or make any updates as necessary.

There is an aliases column in these tables so you can add in aliases for existing entries that you come across.  For example, if you have an entry in **people** for
Henry Charles Albert David, you could add an alias of _Prince Harry_ so that if Spacy extracts that name it will link to the proper existing person.

Entries added to facilities should be linked to a city to establish relationships found there. 

## Notes
I'm currently moving this from using Geonames for locations to something else.  I have created a curated list of cities that I hope to be able to release soon.  There is a lot of
logic built into the application to try to get around inaccuracies in Geonames, and moving it to another database of cities should hopefully allow
me to simplify that.

For now, the logic tries to work around Geonames by finding the countries mentioned in the article, then checking for cities in that country, then trying to 
use the city with the largest population.  Failing that, it will simply pick the city with the largest population that matches the name.
If no matching name is found, it will add the city to the locations table where you can then manually either add in the coordinates and
population or find the real city name and reassign it in **article_locations**.

## Built With
* [Spacy](https://spacy.io/) - The Python NLP processor used
* [Geonames](https://www.geonames.org/) - The locations dataset currently used

## Contributing
Branch, make a pull request, you know the drill.

## Author(s)
* Brian Maddox

## License
This project is licensed under the MIT License.  See the file LICENSE for details.

## Warranties and Guarantees
Ha!  Absolutely not.  Use at your own risk.  It's basically a side research project.
  