import feedparser as fp
import json
import newspaper
from newspaper import Article
from time import mktime
from datetime import datetime
import pathlib
from shutil import copyfile





class NewsScraper:
    def __init__(self, limitNews = 50):
        self.LIMIT = limitNews
        self.data = {}
        self.data['newspapers'] = {}





    def createHTML(self, nowday):

        copyfile('index_head.txt', 'news' + nowday + '.html')
        return open( 'news' + nowday + '.html', "a", encoding='utf8')


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

        pathlib.Path( 'news/' + nowDay ).mkdir(parents=True, exist_ok=True)


        htmlFile = self.createHTML(nowTime)


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
                    htmlFile.write( '\n<h1 style=\'color: white\'>' + company + '</h1>\n' )
                    htmlFile.write( '  <div class="ui inverted segment">\n' )
                    htmlFile.write( '    <div class="ui inverted accordion" style="width:600px;">\n' )
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
                        article['published'] = datetime.fromtimestamp(mktime(date)).isoformat()
                
                        # if the time is out of date, ignore it.
                        if not str(article['published']).startswith( nowDay ):
                            print( 'Got a news but not today: {}, {}'.format(nowDay, article['published']) )
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
                        if htmlFile:
                            htmlFile.write( '      <div class="title"><i class="dropdown icon"></i>' + content.title + '</div>\n' )
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
                paper = newspaper.build(value['link'], memoize_articles=False)
                newsPaper = {
                    "link": value['link'],
                    "articles": []
                }
                noneTypeCount = 0

                # TODO: dump data to each company file
                outputFile = open( 'news/' + nowDay + '/' + company + nowTime + "_sites.txt", "a", encoding='utf8')

                if htmlFile:
                    htmlFile.write( '\n<h1 style=\'color: white\'>' + company + '</h1>\n' )
                    htmlFile.write( '  <div class="ui inverted segment">\n' )
                    htmlFile.write( '    <div class="ui inverted accordion" style="width:600px;">\n' )

                for content in paper.articles:
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
                        if noneTypeCount > 10:
                            print("Too many noneType dates, aborting...")
                            noneTypeCount = 0
                            break
                        count = count + 1
                        continue
                    article = {}
                    article['title'] = content.title
                    article['text'] = content.text
                    article['link'] = content.url
                    article['published'] = content.publish_date.isoformat()

                    # if the time is out of date, ignore it.
                    if not str(article['published']).startswith( nowDay ):
                        print( 'Got a news but not today: {}, {}'.format(nowDay, article['published']) )
                        #count = count - 1
                        continue
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
                        htmlFile.write( '      <div class="title"><i class="dropdown icon"></i>' + content.title + '</div>\n' )
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

        if htmlFile:
            htmlFile.write( '</body>' )
            htmlFile.write( '</html>' )
        # Finally it saves the articles as a JSON-file.
        try:
            with open('news/' + nowDay + '/' + 'scraped_articles' + nowTime + '.json', 'w', encoding='utf8') as outfile:
                json.dump(data, outfile, ensure_ascii=False)
        except Exception as e: print(e)










