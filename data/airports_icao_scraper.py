#!/bin/env python3
import sys
import csv
import re
import string
import requests
import functools
from bs4 import BeautifulSoup


BASE_URL = "https://airportcodes.aero"
LINK_REGEX = re.compile("^/[A-Z0-9]{3,4}$")


if len(sys.argv) < 2:
    print("Missing output CSV file")
    sys.exit(1)


@functools.total_ordering
class Airport:
    name = None
    country = None
    lat = 0
    lon = 0

    def __init__(self, url):
        self.url = url
        self.icao = url.split("/")[-1]

    def __str__(self):
        if self.name:
            return "%s (%s, %s) %s %s" % (self.icao, self.lat, self.lon, self.name, self.country)
        else:
            return self.icao

    def __hash__(self):
        return hash(self.icao)

    def __eq__(self, other):
        return self.icao == other.icao
    def __lt__(self, other):
        return self.icao < other.icao

    def fetch_data(self):
        data = requests.get(BASE_URL + self.url)
        page = BeautifulSoup(data.content, "html.parser")

        for table in page.findAll("table", class_="datagrid fullwidth"):
            for row in page.findAll("tr"):
                name = None
                for data in row.findAll("td"):
                    if not name:
                        name = data.get_text()
                        continue
                    if name == "Name":
                        # print(data)
                        # self.name = data.get_text()
                        self.name = str(data).split("<br/>")[0].split(">")[1]
                    elif name == "Country":
                        self.country = data.get_text()
                    elif name == "Latitude":
                        self.lat = data.get_text().replace("┬░", "°")
                    elif name == "Longitude":
                        self.lon = data.get_text().replace("┬░", "°")
                    break
            if not self.name:
                print(table)

    def get_csv_row(self):
        if not self.name:
            return None
        if not self.country:
            return None
        if (self.lat == 0) or (self.lon == 0):
            return None
        maxdigit = 0
        for c in self.lat + self.lon:
            if c.isdigit():
                maxdigit = max(maxdigit, int(c))
        if maxdigit == 0:
            return None
        display_name = self.name
        if self.country:
            display_name += " (" + self.country + ")"
        return [self.icao, self.lat, self.lon, display_name]



airports = []

for letter in string.ascii_uppercase:
    url = BASE_URL + "/icao/" + letter
    print(url)
    data = requests.get(url)
    page = BeautifulSoup(data.content, "html.parser")

    # Find all airport links on page
    for link in page.findAll("a"):
        if not LINK_REGEX.match(link["href"]):
            continue
        new = Airport(link["href"])
        new.fetch_data()
        airports.append(new)

# Sort and remove duplicates
airports = sorted(list(set(airports)))

# Write to CSV
with open(sys.argv[1], mode='w') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    csvwriter.writerow(["ICAO", "Latitude", "Longitude", "Name"])
    for a in airports:
        try:
            csvwriter.writerow(a.get_csv_row())
            print(a)
        except:
            pass
