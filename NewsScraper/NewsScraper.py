import feedparser as fp
import json
import newspaper
from newspaper import Article
from time import mktime
from datetime import datetime
import pathlib
from shutil import copyfile
from bs4 import BeautifulSoup
import requests




class NewsScraper:
    def __init__(self, limitNews = 30):
        self.LIMIT = limitNews
        self.data = {}
        self.data['newspapers'] = {}

    def getTimeOffset(self, ntime):
        offset = 8
#        print( '-6:' + ntime[-6] )
#        print( '20:21 ' + ntime[20:22] )
#        print( '11:12 ' + ntime[11:13] )
        if ntime[-6] == '+':
            offset = offset - int(ntime[20:22])
        elif ntime[-6] == '-':
            offset = offset + int(ntime[20:22])

        nCSTTime = ntime[0:11]
        if int(ntime[11:13]) + offset >= 7 and int(ntime[11:13]) + offset <= 22:
            nCSTTime += '%02d' % (int(ntime[11:13]) + offset)
            nCSTTime += ntime[13:19]
            nCSTTime += '+08:00'
        else:
            nCSTTime += ntime[11:]
        return nCSTTime




    def createHTML(self, nowday):

        copyfile('index_head.txt', 'news' + nowday + '.html')
        return open( 'news' + nowday + '.html', "a", encoding='utf8')

    def getHTMLTail(self):
        return open( 'index_tail.txt', "r", encoding='utf8')
		
		
    # Get web page
    def get_web_page(self, url):
        resp = requests.get(
            url=url,
            cookies={'over18': '1'}
        )
        if resp.status_code != 200:
            print('Invalid url:', resp.url)
            return None
        else:
            return resp.text

    def parsing_SETN_news(self, url):
	
        news_url_list = []
        soup = BeautifulSoup(self.get_web_page(url), 'html.parser')
        news_list_div = soup.find_all('div', class_="NewsList")
        for news in news_list_div[0].find_all('a'):

            if news['href'].find('NewsID') < 0:
                continue
 
            news_url_list.append('https://www.setn.com' + news['href'])
        return news_url_list
		
    def parsing_CNA_news(self, url):
	
        news_url_list = []
        soup = BeautifulSoup(self.get_web_page(url), 'html.parser')
        news_list_div = soup.find_all('div', class_=['subHalf', 'menuUrl'])
        for news in news_list_div[0].find_all('a'):

            if news.get('href') == None:
                continue
 
            news_url_list.append(news['href'])
        print(news_url_list)
        return news_url_list
		
    def parsing_LTN_news(self, url):
	
        news_url_list = []
        soup = BeautifulSoup(self.get_web_page(url), 'html.parser')
        news_list_div = soup.find_all('div', class_=['whitecon'])
        for news in news_list_div[0].find_all('a', class_='tit' ):

            if news.get('href') == None:
                continue
 
            news_url_list.append('https:' + news['href'])
        print(news_url_list)
        return news_url_list

    def parsing_CHINATIMES_news(self, url):
	
        news_url_list = []
        soup = BeautifulSoup(self.get_web_page(url), 'html.parser')
        news_list_div = soup.find_all('div', class_=['listRight'])
        for news_title in news_list_div[0].find_all('h2'):
            for news in news_title.find_all('a'):
                if news.get('href') == None:
                    continue

                news_url_list.append('https://www.chinatimes.com' + news.get('href'))
        print(news_url_list)
        return news_url_list




# Set the limit for number of articles to download
#LIMIT = 50

#data = {}
#data['newspapers'] = {}

    def startParsingNews(self):

        # Loads the JSON files with news sites
        data = {}
        data['newspapers'] = {}
        with open('NewsPapers.json') as data_file:
            companies = json.load(data_file)

        count = 1

        nowDay = datetime.now().strftime( '%Y-%m-%d' )
        nowTime = datetime.now().strftime( "_%Y-%m-%d_%H-%M-%S" )
        grabedTimeCheck = datetime.now().strftime( "%Y-%m-%dT" )
        grabedTimeCheckHour = int(datetime.now().strftime( "%H" )) - 1
        grabedTimeCheck += '%02d' % grabedTimeCheckHour

        pathlib.Path( 'news/' + nowDay ).mkdir(parents=True, exist_ok=True)


        htmlFile = self.createHTML(nowTime)
        htmlTailContent = self.getHTMLTail().read()


        # Iterate through each news company
        for company, value in companies.items():
            # If a RSS link is provided in the JSON file, this will be the first choice.
            # Reason for this is that, RSS feeds often give more consistent and correct data.
            # If you do not want to scrape from the RSS-feed, just leave the RSS attr empty in the JSON file.
            if 'rss' in value:
                d = fp.parse(value['rss'])
                print("Downloading articles from ", company)
                newsPaper = {
                    "rss": value['rss'],
                    "link": value['link'],
                    "articles": []
                }



                # TODO: dump data to each company file
                outputFile = open( 'news/' + nowDay + '/' + company + nowTime + "_rss.txt", "a", encoding='utf8')
                if htmlFile:
                    htmlFile.write( '\n<h1>' + company + '</h1>\n' )
                    htmlFile.write( '  <div class="ui segment" style=" color: #FFF4E0; background-color: #393E46">\n' )
                    htmlFile.write( '    <div class="ui accordion" style="width:600px; color: #FFF4E0; background-color: #393E46">\n' )
#               outputFile = open( 'index_', "a", encoding='utf8')
                for entry in d.entries:
                    # Check if publish date is provided, if no the article is skipped.
                    # This is done to keep consistency in the data and to keep the script from crashing.
                    if hasattr(entry, 'published'):
                        if count > self.LIMIT:
                            break
                        article = {}
                        article['link'] = entry.link
                        date = entry.published_parsed
                        print('origin:' + datetime.fromtimestamp(mktime(date)).isoformat())
                        newTimeOffset = self.getTimeOffset(datetime.fromtimestamp(mktime(date)).isoformat())
                        article['published'] = newTimeOffset
                
                        # if the time is out of date, ignore it.
                        if not str(article['published']).startswith( nowDay ):
                            print( 'Got a news but not today: {}, {}'.format(nowDay, article['published']) )
                            continue
                        if not str(article['published']).startswith( grabedTimeCheck ):
                            print( 'Got a news but not this hour: {}, {}'.format(grabedTimeCheck, article['published']) )
                            #count = count - 1
                            continue
                        try:
                            content = Article(entry.link)
                            content.download()
                            content.parse()
                        except Exception as e:
                            # If the download for some reason fails (ex. 404) the script will continue downloading
                            # the next article.
                            print(e)
                            print("continuing...")
                            continue
                        article['title'] = content.title
                        article['text'] = content.text
                        newsPaper['articles'].append(article)
                        print(count, "articles downloaded from", company, ", url: ", entry.link)
                        count = count + 1
                        # TODO: dump data to each company file
                        if outputFile:
                            outputFile.write( '-----' + str(count - 1) + '-----\n' )
                            outputFile.write( '***** ' + content.title + ' *****\n\n' )
                            outputFile.write( content.text + '\n\n' )
                            outputFile.write( entry.link + '\n\n' )
                            outputFile.write( article['published'] + '\n\n' )
                        if htmlFile:
                            htmlFile.write( '      <div class="title" style="color: #FFF4E0;"><i class="dropdown icon" style="color: #f8b500;"></i>' + content.title + '</div>\n' )
                            htmlFile.write( '      <div class="content">\n' )
                            htmlFile.write( '        <a href="' + entry.link + '" target="_blank"><blockquote>NEWS link</blockquote></a>\n' )
                            htmlFile.write( '        <p class="transition hidden"><blockquote>Published time: ' + article['published'] + '</blockquote></p>\n' )
                            formattedText = content.text.replace( "\n", "<br>" )
                            htmlFile.write( '        <p class="transition hidden"><blockquote>' + formattedText + '</blockquote></p>\n' )
                            htmlFile.write( '      </div>\n' )
                if htmlFile:
                    htmlFile.write( '    </div>' )
                    htmlFile.write( '  </div>' )
            else:
                # This is the fallback method if a RSS-feed link is not provided.
                # It uses the python newspaper library to extract articles
                print("Building site for ", company)
#self.get_web_page(value['link'])

                if company == 'setn':
                    news_list_url = self.parsing_SETN_news(value['link'])
                elif company == 'cna':
                    news_list_url = self.parsing_CNA_news(value['link'])
                elif company == 'ltn':
                    news_list_url = self.parsing_LTN_news(value['link'])
                elif company == 'chinatimes':
                    news_list_url = self.parsing_CHINATIMES_news(value['link'])

   #             soup = BeautifulSoup(self.get_web_page(value['link']), 'html.parser')
   #             news_list_div = soup.find_all('div', class_="NewsList")

                #paper = newspaper.build(value['link'])
                newsPaper = {
                    "link": value['link'],
                    "articles": []
                }
                noneTypeCount = 0

                # TODO: dump data to each company file
                outputFile = open( 'news/' + nowDay + '/' + company + nowTime + "_sites.txt", "a", encoding='utf8')

                if htmlFile:
                    htmlFile.write( '\n<h1>' + company + '</h1>\n' )
                    htmlFile.write( '  <div class="ui segment" style=" color: #FFF4E0; background-color: #393E46">\n' )
                    htmlFile.write( '    <div class="ui accordion" style="width:600px; color: #FFF4E0; background-color: #393E46">\n' )
                for news in news_list_url:
                    try:
                        content = Article(news)
                        content.download()
                        content.parse()
                    except Exception as e:
                           # If the download for some reason fails (ex. 404) the script will continue downloading
                            # the next article.
                        print(e)
                        print("continuing...")
                        continue
	
    #print(content.title)
 #               for content in paper.articles:
                    if count > self.LIMIT:
                        break
                    try:
                        content.download()
                        content.parse()
                    except Exception as e:
                        print(e)
                        print("continuing...")
                        continue
                    # Again, for consistency, if there is no found publish date the article will be skipped.
                    # After 10 downloaded articles from the same newspaper without publish date, the company will be skipped.
                    if content.publish_date is None:
                        print(count, " Article has date of type None...")
                        noneTypeCount = noneTypeCount + 1
                        content.publish_date = "2018-10-10 0900"
                        break
                        if noneTypeCount > 30:
                            print("Too many noneType dates, aborting...")
                            noneTypeCount = 0
                            break
                        count = count + 1
                        continue
                    article = {}
                    article['title'] = content.title
                    article['text'] = content.text
                    article['link'] = content.url
                    print('origin:' + content.publish_date.isoformat())
                    newTimeOffset = self.getTimeOffset(content.publish_date.isoformat())
                    article['published'] = newTimeOffset

                    # if the time is out of date, ignore it.
                    #if not str(article['published']).startswith( nowDay ):
                    #    print( 'Got a news but not today: {}, {}'.format(nowDay, article['published']) )
                        #count = count - 1
                    #    continue
                    #if not str(article['published']).startswith( grabedTimeCheck ):
                    #    print( 'Got a news but not this hour: {}, {}'.format(grabedTimeCheck, article['published']) )
                    #    #count = count - 1
                    #    continue
                    newsPaper['articles'].append(article)
                    print(count, "articles downloaded from", company, " using newspaper, url: ", content.url)
                    count = count + 1
                    noneTypeCount = 0
                    # TODO: dump data to each company file
                    if outputFile:
                        outputFile.write( '-----' + str(count - 1) + '-----\n' )
                        outputFile.write( '***** ' + content.title + ' *****\n\n' )
                        outputFile.write( content.text + '\n\n' )
                        outputFile.write( content.url + '\n\n' )
                        outputFile.write( content.publish_date.isoformat() + '\n\n' )
                    if htmlFile:
                        htmlFile.write( '      <div class="title" style="color: #FFF4E0;"><i class="dropdown icon" style="color: #f8b500;"></i>' + content.title + '</div>\n' )
                        htmlFile.write( '      <div class="content">\n' )
                        htmlFile.write( '        <a href="' + content.url + '" target="_blank"><blockquote>NEWS link</blockquote></a>\n' )
                        htmlFile.write( '        <p class="transition hidden"><blockquote>Published time: ' + content.publish_date.isoformat() + '</blockquote></p>\n' )
                        formattedText = content.text.replace( "\n", "<br>" )
                        htmlFile.write( '        <p class="transition hidden"><blockquote>' + formattedText + '</blockquote></p>\n' )
                        htmlFile.write( '      </div>\n' )
                if htmlFile:
                    htmlFile.write( '    </div>' )
                    htmlFile.write( '  </div>' )
            count = 1
            data['newspapers'][company] = newsPaper

        if not htmlTailContent:
            htmlFile.write( '</body>' )
            htmlFile.write( '</html>' )
        else:
            htmlFile.write( htmlTailContent )
        # Finally it saves the articles as a JSON-file.
        try:
            with open('news/' + nowDay + '/' + 'scraped_articles' + nowTime + '.json', 'w', encoding='utf8') as outfile:
                json.dump(data, outfile, ensure_ascii=False)
        except Exception as e: print(e)










