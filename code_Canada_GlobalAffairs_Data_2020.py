import os
import pandas as pd
import sys
import re
from bs4 import BeautifulSoup  # for html with beautifulsoup
from selenium import webdriver  # for driver use

os.chdir("/Users/arishleyka/Dropbox/399R Sandy/")
driver = webdriver.Chrome(executable_path='/Users/arishleyka/chromedriver')  # version must update version of chrome being used

# define the followings first in order to make functions
url_ns = "https://www.canada.ca/en/news/advanced-news-search.html"
driver.get(url_ns)
html = driver.page_source
soup = BeautifulSoup(html, features="lxml")
sys.setrecursionlimit(5000)  # needed since the for loop runs more than the default max recursions


########################################
##### defining functions for each article
########################################

def get_title():
    for read in soup.find(id='wb-cont'):
        return read


def stripped_text():  # separates the text from the unnecessary info at the top of the article and puts it into a list
    first = '—'
    second = '-'
    date_text = 'Global Affairs'
    news_release = soup.find(id='news-release-container')  # media advisories have a diff html tree
    first_par = soup.find(class_="cmp-text")
    for entirety in soup.find_all(
            class_="cmp-text"):
        entire_text = entirety.text.strip()
        if 'Media advisory' in news_release.find('h2').text:
            paragraphs = entire_text.split('-')
            return paragraphs
        elif first_par.find(attrs={'text': True}):
            if second in first_par.p.text:
                paragraphs = entire_text.split('-')
                return paragraphs
            elif first in first_par.p.text:
                paragraphs = entire_text.split('—')
                return paragraphs
            elif date_text not in first_par.p.text and '2020' not in first_par.p.text:  # for articles that don't have the date or location inside of the text
                paragraphs = entire_text
                return paragraphs
            elif '2020' in first_par.p.text:
                paragraphs = entire_text.split('–')
                paragraphs = ''.join(paragraphs).split('\n')
                return paragraphs
        elif second in entire_text:
            paragraphs = entire_text.split('-')
            return paragraphs
        elif first in entire_text:
            paragraphs = entire_text.split('—')
            return paragraphs
        else:
            paragraphs = entire_text
            return paragraphs


def get_text():  # takes the separated text in a list and joins it where necessary
    stripped_text()
    date_text = 'Global Affairs Canada'
    year = '2020'
    year_w = ', 2020'
    news_release = soup.find(id='news-release-container')
    if 'Media advisory' in news_release.find('h2').text:  # since media advisory has a different structure
        paragraph_text = ''.join(stripped_text()[1:])
        return paragraph_text
    elif len(stripped_text()) > 2 and date_text in stripped_text()[2]:
        paragraph_text = ''.join(stripped_text()[2:])
        paragraph_text = paragraph_text.replace('Global Affairs Canada', '', 1).replace('\n', '')
        return paragraph_text
    elif len(stripped_text()) == 2 and year in stripped_text()[1]:
        paragraph_text = ''.join(stripped_text())
        paragraph_text = paragraph_text.split(",")
        paragraph_text = ''.join(paragraph_text[2:]).replace('Global Affairs Canada', '', 1).replace('\n', '')
        paragraph_text = re.sub("2020", "", paragraph_text, count=1)
        return paragraph_text
    if year_w in stripped_text()[0]:
        paragraph_text = ''.join(stripped_text()[1:]).replace('\n', '').replace('Global Affairs Canada', '', 1)
        return paragraph_text
    else:
        paragraph_text = ''.join(stripped_text()).replace('\n', '').replace('Global Affairs Canada', '', 1)
        return paragraph_text


######loop through each page

article_links = []  # where the links will be stored
article_info = []  # where the info from the second for loop is stored
article_list = []  # where the info from the first for loop is stored
for i in range(0, 440, 10):  # range (0,440,10)
    url = "https://www.canada.ca/en/news/advanced-news-search/news-results.html?start=2020-01-01&end=2020-12-31&idx=" + str(
        i) + "&_=1613604715685&dprtmnt=departmentofforeignaffairstradeanddevelopment"
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, features="lxml")
    article_links = [a['href'] for a in soup.select('.h5 a')]
    biography = soup.find(text=re.compile('Biographical'))  # finds biographical articles
    biography = str(biography)  # converts the class from bs4 navigable string to a string to be used in the if statement
    entire_text_soup = soup.get_text()
    if biography in entire_text_soup:  # removes biographical articles
        pass
    else:

        for article in soup.find_all('article', class_='item'):
            times = article.find('time')
            links = [a.attrs['href'] for a in article.select('.h5 a')]
            date = times.text
            year = date.split("-")[0]
            previous = times.next_sibling
            doctype = previous.replace('| Global Affairs Canada', '').strip().lstrip("|")
            title = article.find(class_='h5').text

            each_article_in_list = {
                'title': title,
                'links': links,
                'date': date,
                'year': year,
                'doctype': doctype
            }

            print('Saving: ', each_article_in_list['title'])
            article_list.append(each_article_in_list)

        for article in article_links:
            url = article
            driver.get(url)
            html = driver.page_source
            soup = BeautifulSoup(html, features="lxml")

            get_title()
            get_text()

            each_article = {
                'title': get_title(),
                'text': get_text()
            }

            print('Saving: ', each_article['title'])  # proof its working, not nec.
            article_info.append(each_article)


df_article_info = pd.DataFrame(article_info)
df_article_list = pd.DataFrame(article_list)

df = pd.merge(df_article_list, df_article_info, on="title")  # merges the two dataframes by title of the article

df.columns = [col.replace('_x', '') for col in df.columns]
df.columns = [col.replace('_y', '') for col in df.columns]

df['links'] = df['links'].str.get(0)  # removes the brackets around the links
print(df.head(5))
df.to_csv('code_Canada_GlobalAffairs_Data.csv')
