from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import math
import csv
from pathlib import Path

CSV_HEADERS = ["#", "Player", "Season", "Team", "Shoots", "Pos", "GP", "G", "A", "P", "+/-", "PIM", "P/GP", "EVG", "EVP",
              "PPG", "PPP", "SHG", "SHP", "OTG", "GWG",
              "S", "S%", "TOI/GP", "FOW%"]

def scrape_nhl_standings(csv_dump_path, season):
    try:
        driver = webdriver.Chrome()

        for year in range(season[0], season[1]):
            driver.get(build_url(year))

            set_page_size_to_100(driver)

            players_standings = []
            driver.implicitly_wait(100)
            next_page_button = driver.find_element(By.CLASS_NAME, "-next").find_element(By.TAG_NAME, "button")

            while next_page_button.get_attribute("disabled") is None:
                table_standings_page = driver.find_element(By.CLASS_NAME, "rt-tbody")
                players_standings += parse_standings_page(table_standings_page.text)
                next_page_button.click()
                driver.implicitly_wait(100)
                next_page_button = driver.find_element(By.CLASS_NAME, "-next").find_element(By.TAG_NAME, "button")

            write_to_csv(csv_dump_path, players_standings, year)
            print("Finished season {0}-{1}".format(year, year+1))

    finally:
        # noinspection PyUnboundLocalVariable
        driver.close()


def build_url(seasons_start_year):
    year_string = str(seasons_start_year) + str(seasons_start_year+1)

    return "http://www.nhl.com/stats/skaters?reportType=season" \
           "&seasonFrom={0}" \
           "&seasonTo={0}" \
           "&gameType=2" \
           "&filter=gamesPlayed,gte,1" \
           "&sort=points,goals,assists".format(year_string)


def set_page_size_to_100(driver):
    page_size_dropdown = Select(driver
                                .find_element(By.CLASS_NAME, "-pageSizeOptions")
                                .find_element(By.TAG_NAME, "select"))

    page_size_dropdown.select_by_value("100")


def parse_standings_page(standings):
    players_standings = []
    cells = standings.split('\n')

    rows_count = len(cells) // len(CSV_HEADERS)

    if not rows_count - math.floor(rows_count) == 0:
        raise ValueError("Cells count isn't divisible by cells per row.")

    for i in range(0, int(rows_count)):
        players_standings.append(cells[i * len(CSV_HEADERS): (i + 1) * len(CSV_HEADERS)])

    return players_standings


def write_to_csv(csv_dump_path, players_standings, year):
    with open(str(csv_dump_path / "{0}-{1}.csv".format(year, year+1)), "w+", newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=",")
        csvwriter.writerow(CSV_HEADERS)
        csvwriter.writerows(players_standings)


if __name__ == "__main__":
    csv_path = Path(__file__).parent / 'statistics'

    if not csv_path.exists():
        csv_path.mkdir()

    for i in range(2015,2022):
        scrape_nhl_standings(csv_path, season=(i, i+1))