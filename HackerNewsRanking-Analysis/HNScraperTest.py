"""
HackerNews webscraper, basic structure inspiration from by Caleb Pollan,
heavily modified output and additional parsing methods by Adam Miles.

Collects and returns data on each article, to assist in determining what
features might help an article retain a top rank/front page position on the
HackerNews website.
"""

import csv
import datetime
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


def get_driver():
    """Gets and returns the appropriate webdriver."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    return webdriver.Chrome(
        executable_path=r'/usr/local/bin/chromedriver', chrome_options=options)


def connect_to_base(browser, page_number):
    """ Establishes the connection to a HackerNews page.

        Connects to the requested page number (incremented in main) of
        of Hacker News. Timeout occurs after 3 attempts.

        Args:
            browser (browser): the browser driver (in this case chromedriver)
            page_number (int): an integer representing the requested page number

        Returns:
            False if connection fails 3 attempts, true if connection succesful.
    """

    base_url = f'https://news.ycombinator.com/news?p={page_number}'
    connection_attempts = 0
    while connection_attempts < 3:
        try:
            browser.get(base_url)
            WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.ID, 'hnmain'))
            )
            return True
        except Exception:
            connection_attempts += 1
            print(f'Error connecting to {base_url}.')
            print(f'Attempt #{connection_attempts}.')
    return False


def parse_age(age):
    """ Parses the age string of the article to hours.

        Input string may include the time in hours, minutes, days, or may not be
        available (will fail conversion to float).

        Args:
            age (string): text describing the age of an article.

        Returns:
            age_in_hours (float): the age of the article in hours, or "NA" if
                not available or unable to convert to float.

    """
    age_set = age.split(' ')
    age_in_hours = 0
    try:
        age_in_hours = float(age_set[0])
    except ValueError:
        age_in_hours = "NA"
    if (age_set[1] == "days"):
        age_in_hours *= 24
    elif (age_set[1] == "minutes"):
        age_in_hours /= 60

    return age_in_hours


def parse_comments(comment):
    """ Parses and returns the number of comments for a post."""

    if (comment == "discuss"):
        comments_count = 0

    try:
        comments_count = float(comment)
    except ValueError:
        comments_count = "NA"

    return comments_count


def parse_html(html):
    """ Parses the html content of a HackerNews page.

        Scrapes and catelogues the following key metrics for each post.
            'comments' (int): the number of comments for the post.
            'rank' (int): the rank of the post.
            'score' (int): the score of the post.
            'age' (float): the age of the article in hours.
            'title_length': the length of the title in characters.

        Args:
            html ([string]): The source html of a target webpage.

        Returns:
            output_list ([string]): The list of results, in the format:
                ['comments', 'rank', 'score', 'age', 'title_length']
                [int, int, int, float, int]
    """
    soup = BeautifulSoup(html, 'html.parser')
    output_list = []
    entry_tr = soup.find_all('tr', class_='athing')
    entry_td = soup.find_all('td', class_='subtext')

    for x in range(0, len(entry_tr)):

        article_id = entry_tr[x].get('id')
        try:
            article_age = soup.find(href=f'item?id={article_id}').string
        except IndexError:
            article_age = "NA"
        try: 
            score = soup.find(id=f'score_{article_id}').string
        except Exception:
            score = '0 points'
        try:
            comments = entry_td[x].find_all('a').pop().string.split("\xa0")[0]

        except Exception:
            comments = 0

        article_info = {
            'comments': parse_comments(comments),
            'rank': float(entry_tr[x].span.string),
            'score': int(score.split(" ")[0]),
            'age': parse_age(article_age),
            'title_length': len(entry_tr[x].find(class_='storylink').string),
        }
        output_list.append(article_info)

    return output_list


def write_to_file(output_list, filename):
    """ Writes the results"""
    with open(filename, 'a') as csvfile:
        fieldnames = ['comments', 'rank', 'score', 'age', 'title_length']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for row in output_list:
            writer.writerow(row)


def run_process(page_number, filename, browser):
    """ Runs the main scraping and results handilng process for each page."""
    if connect_to_base(browser, page_number):
        # follows robots.txt rules.
        sleep(2)
        html = browser.page_source
        output_list = parse_html(html)
        write_to_file(output_list, filename)
    else:
        print('Error connecting to hackernews')


if __name__ == '__main__':
    """ Main method sets up script parameters and starts the script."""
    # set the range of pages to scrape.
    page = 1
    max_pages = 5
    # timestamp is used for naming the files for easy catelogueing and sorting.
    scrape_timestamp = datetime.datetime.now().strftime('%Y-%m-%d%-H%M%S')
    output_filename = f'{scrape_timestamp}.csv'
    browser = get_driver()
    with open(output_filename, 'a') as csvfile:
        fieldnames = ['comments', 'rank', 'score', 'age', 'title_length']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    while page <= max_pages:
        print(f'Analyzing page #{page}...')
        run_process(page, output_filename, browser)
        page = page + 1

    browser.quit()
