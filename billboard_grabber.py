import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# importing keys from .env file
load_dotenv(os.path.join(os.getcwd(), '.env'))

# https://www.officialcharts.com/charts/rock-and-metal-singles-chart/20240426/111/


class BillboardGrabber:
    def __init__(self):
        self.BASE_URL_BILLBOARD = "https://www.billboard.com/charts/hot-100/"
        self.search_date = input("Enter the date you want to search top-100 most popular songs, in format YYYY-MM-DD >>> ")

        # self.search_date = "YYYY-MM-DD"
        self.playlist_name = f"Top 100 picks for {self.search_date}"
        self.scrapped_billboard = requests.get(self.BASE_URL_BILLBOARD + self.search_date + "/").content
        self.billboard_soup = BeautifulSoup(self.scrapped_billboard, "html.parser")

        self.song_results = self.billboard_soup.find_all("div", class_="o-chart-results-list-row-container")
        self.song_dict = {}

        for number, item in enumerate(self.song_results):
            self.song_author = item.find("li", class_="lrv-u-width-100p").find("span").getText().replace("\n", "").replace("\t", "")
            self.song_name = item.find("h3").getText().replace("\n", "").replace("\t", "")
            self.song_dict[number+1] = [self.song_author, self.song_name]

        print(self.song_dict)
