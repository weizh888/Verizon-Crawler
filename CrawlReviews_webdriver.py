#!/usr/bin/python
# -*- coding: utf-8 -*-

# __author__ = "Wei Zhang"

import os
import time
from datetime import datetime

import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import seaborn as sns
from pprint import pprint


def setup():
    driver = webdriver.Chrome(executable_path=r'chromedriver')
    driver.set_window_size(1680, 1050)
    return driver


def check_results_dir():

    # create results folder

    if not os.path.exists('results'):
        os.makedirs('results')


def login(username, password, driver=None):
    driver.get('https://oauth.sysomos.com/oauth/login.jsp')
    usr_btn = driver.find_element_by_name('j_username')
    pwd_btn = driver.find_element_by_name('j_password')
    submit_btn = driver.find_element_by_name('login')

    usr_btn.send_keys(username)
    pwd_btn.send_keys(password)
    submit_btn.click()
    print driver.current_url
    return driver


def set_sessions(driver):
    request = requests.Session()
    headers = \
        {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'}

    request.headers.update(headers)
    cookies = driver.get_cookies()
    for cookie in cookies:
        request.cookies.set(cookie['name'], cookie['value'])
    return request


def wait_til_clickable(driver, xpath):
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    return driver


if __name__ == '__main__':

    timetag = datetime.now().strftime('%Y%m%d-%H%M%S')  # add timestamp to filenames
    driver = login('ye.ouyang@Verizonwireless.com', '20Independence#',
                   setup())
    rq = set_sessions(driver)

    # Click search button

    search_xpath = \
        '/html/body/sys-sso-navigation/div/div/o-navigation-list/ul/li[1]/o-navigation-item-link/a/i'
    wait_til_clickable(driver, search_xpath)
    search_click = driver.find_elements_by_xpath(search_xpath)
    search_click[0].click()
    print driver.current_url

    # Apply two filters: country - USA & language - ENG

    country_xpath = '//*[@id="filters-listing"]/div/section[1]/div[1]/a'
    wait_til_clickable(driver, country_xpath)
    driver.find_element_by_xpath(country_xpath).click()
    usa_xpath = \
        '//*[@id="filters-listing"]/div/section[1]/div[2]/div[3]/div[1]/article[10]/a'
    wait_til_clickable(driver, usa_xpath)
    driver.find_element_by_xpath(usa_xpath).click()

    # print driver.current_url

    apply_btn_xpath = '//*[@id="filter-apply"]'
    wait_til_clickable(driver, apply_btn_xpath)
    driver.find_element_by_xpath(apply_btn_xpath).click()
    print driver.current_url

    back_btn_xpath = '//*[@id="filter-back"]'
    driver.find_element_by_xpath(back_btn_xpath).click()
    print driver.current_url

    language_xpath = \
        '//*[@id="filters-listing"]/div/section[7]/div[1]/a'
    wait_til_clickable(driver, language_xpath)
    driver.find_element_by_xpath(language_xpath).click()
    eng_xpath = \
        '//*[@id="filters-listing"]/div/section[7]/div[2]/div[3]/div[1]/article[2]/a'
    wait_til_clickable(driver, eng_xpath)
    driver.find_element_by_xpath(eng_xpath).click()

    apply_btn_xpath = '//*[@id="filter-apply"]'
    wait_til_clickable(driver, apply_btn_xpath)
    driver.find_element_by_xpath(apply_btn_xpath).click()
    print driver.current_url

    driver.find_element_by_xpath('//*[@id="filters-container"]/a[1]/span'
                                 ).click()

    # Add keyword - Verizon
    keyword = 'Verizon'
    keyword_xpath = '//*[@id="simple-query-keywords"]/div/div/div/input'
    kw_btn = driver.find_element_by_xpath(keyword_xpath)
    kw_btn.send_keys(keyword)
    driver.find_element_by_xpath('//*[@id="simple-query-keywords"]/div/div/div/span'
                                 ).click()

    # Search & Analytics
    driver.find_element_by_xpath('//*[@id="submitQueryButton"]').click()
    driver.find_element_by_xpath('//*[@id="query-builder"]/div[2]/div/div/div[1]/div/div[2]/div[2]/ul/li[2]/a'
                                 ).click()

    time.sleep(5)
    driver.execute_script('angular.reloadWithDebugInfo();')
    time.sleep(1)
    wait_til_clickable(driver, '//*[@id="submitQueryButton"]')
    time.sleep(1)
    driver.find_element_by_xpath('//*[@id="submitQueryButton"]').click()
    driver.find_element_by_xpath('//*[@id="query-builder"]/div[2]/div/div/div[1]/div/div[2]/div[2]/ul/li[2]/a'
                                 ).click()
    print driver.current_url

    # Load the whole page by scrolling down to the bottom
    scroll_pause_time = 5
    section_titles = [
        'Latest Activity',
        'OVERALL SENTIMENT',
        'GEOGRAPHY',
        'BUZZ GRAPH',
        'WORD CLOUD',
        'MENTIONS',
        ]
    headings = driver.find_elements_by_class_name('panel-heading')  # get all the headings

    # print(headings)

    for i in range(len(headings)):
        driver.execute_script('arguments[0].scrollIntoView();',
                              headings[i])
        time.sleep(scroll_pause_time)

    # 1. Daily Mentions #
    check_results_dir()
    dm_data = \
        driver.execute_script("return angular.element('sys-widget-latest-activity').scope().data;"
                              )

    # pprint(dm_data)
    # pprint(dm_data['query1']['sources'])

    source_names = []
    daily_mentions = pd.DataFrame()
    for elem in dm_data['query1']['sources']:
        source_name = elem['source']
        daily_mentions[source_name] = pd.Series([int(elemm['mention'])
                for elemm in elem['mentions']])
        source_names.append(source_name)

    # timestamp format: 1496808000000L, long type, needs to be divided by 1000

    daily_mentions['days'] = \
        pd.Series([datetime.fromtimestamp(x['dateTime']
                  / 1000).strftime('%Y-%m-%d') for x in dm_data['query1'
                  ]['sources'][0]['mentions']])
    daily_mentions['ALL SOURCES'] = \
        daily_mentions[source_names].sum(axis=1)
    dm_fields = ['days'] + source_names + ['ALL SOURCES']
    daily_mentions = daily_mentions[dm_fields]
    daily_mentions.rename(columns={'TWITTER_GRID': 'TWITTER',
                          'INSTAGRAM_GRID': 'INSTAGRAM'}, inplace=True)
    print daily_mentions
    daily_mentions.to_csv(r"results/quiz1_1_" + timetag + '.csv',
                          index=False)

    # plot of daily mentions

    daily_mentions.set_index('days', inplace=True)
    daily_mentions.plot()
    plt.xlabel('Day')
    plt.ylabel('Mentions #')
    plt.title('Plot of Daily Mentions #')
    plt.tight_layout()
    plt.savefig(r"results/quiz1_1_" + timetag + '.png', dpi=300)
    print '====================Problem 1 solved===================='

    # 2. Sentiment Score Data
    (sentiment, posPercent, neuPercent, negPercent) = ([], [], [], [])
    sentiment_data = \
        driver.execute_script("return angular.element('sys-widget-sentiment-overall').scope().data;"
                              )

    # pprint(sentiment_data)

    for row in sentiment_data['query1']:
        sentiment.append(row['searchSource'])
        posPercent.append(row['posTotalPerDecimal'])
        neuPercent.append(row['neuTotalPerDecimal'])
        negPercent.append(row['negTotalPerDecimal'])
    ordered_fields = ['Sentiment', 'Positive', 'Neutral', 'Negative']
    sentiment_score = pd.DataFrame({
        'Sentiment': sentiment,
        'Positive': posPercent,
        'Neutral': neuPercent,
        'Negative': negPercent,
        }, columns=ordered_fields)

    # sentiment_score = sentiment_score[ordered_fields]

    print sentiment_score
    sentiment_score.to_csv(r"results/quiz1_2_" + timetag + '.csv',
                           index=False)

    # plot the data to compare with the original graph

    (fig, ax) = plt.subplots()
    bar_width = 0.8
    ind = range(len(sentiment_score['Sentiment']))
    p1 = plt.barh(ind, sentiment_score['Positive'], bar_width,
                  color='#2ecc71')
    p2 = plt.barh(ind, sentiment_score['Neutral'], bar_width,
                  left=sentiment_score['Positive'], color='#95a5a6')
    p3 = plt.barh(ind, sentiment_score['Negative'], bar_width,
                  left=sentiment_score['Positive']
                  + sentiment_score['Neutral'], color='#e74c3c')
    plt.xlabel('Percentage')
    plt.yticks(ind, sentiment_score['Sentiment'])
    plt.gca().invert_yaxis()
    lgd = plt.legend((p1, p2, p3), ('Positive', 'Neutral', 'Negative'),
                     loc='center left', bbox_to_anchor=(1, 0.5))
    plt.title('Sentiment Score')
    plt.tight_layout()
    plt.savefig(r"results/quiz1_2_" + timetag + '.png', dpi=300,
                bbox_extra_artists=(lgd, ), bbox_inches='tight')
    print '====================Problem 2 solved===================='

    # 3. Word Cloud Picture
    while not driver.find_elements_by_class_name('wordcloud-container'):
        time.sleep(1)

    # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "wordcloud-container")))

    word_cloud_elem = \
        driver.find_elements_by_class_name('wordcloud-container')[0]
    driver.execute_script("arguments[0].scrollIntoView(); $('sys-header').remove();"
                          , word_cloud_elem)
    while not word_cloud_elem.find_elements_by_class_name('word-cloud-canvas'
            ):
        time.sleep(1)

    location = word_cloud_elem.location
    size = word_cloud_elem.size
    driver.save_screenshot(r"results/quiz1_3_screenshot_" + timetag
                           + '.png')

    im = Image.open(r"results/quiz1_3_screenshot_" + timetag + '.png')  # uses PIL library to open image in memory

    left = int(location['x'])
    top = int(location['y'])
    right = int(location['x'] + size['width'])
    bottom = int(location['y'] + size['height'])

    im = im.crop((left, top, right, bottom))  # defines crop points
    im.save(r"results/quiz1_3_cropped_" + timetag + '.png')  # saves new cropped image
    print '====================Problem 3 solved===================='

    # 4. Latest Mentions
    soup = BeautifulSoup(driver.page_source.encode('utf8'),
                         'html.parser')
    all_mentions = soup.find_all('div', {'class': 'latestMention'})

    # print(len(all_mentions))

    (mention_name, mention_content, mention_country) = ([], [], [])
    (mention_authority, mention_time, mention_date) = ([], [], [])
    for elem in all_mentions:
        mention_name.append(elem.find(class_='username'
                            ).get_text().strip())
        mention_content.append(elem.find(class_='mentionContent'
                               ).get_text().strip())
        mention_country.append(elem.find(class_='country'
                               ).get_text().strip())
        mention_authority.append(elem.find(class_='authority'
                                 ).get_text().strip())
        mention_time.append(elem.find(class_='time').get_text().strip())
        mention_date.append(elem.find(class_='date').get_text().strip())

    # save latest mentions in dataframe

    mention_fields = [
        'username',
        'content',
        'country',
        'authority',
        'time',
        'date',
        ]
    latest_mentions = pd.DataFrame({
        'username': mention_name,
        'content': mention_content,
        'country': mention_country,
        'authority': mention_authority,
        'time': mention_time,
        'date': mention_date,
        }, columns=mention_fields)

    latest_mentions.to_csv(r"results/quiz1_4_" + timetag + '.csv',
                           index=False, encoding='utf-8')

    print latest_mentions.to_string()
    print '====================Problem 4 solved===================='

    # print(soup.prettify().encode('utf8'))

    driver.quit()
