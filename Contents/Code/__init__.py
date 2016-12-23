# MST3K Plex Channel Plug-in
# Revised: 12-22-2016
import random
DEVELOPMENT = False

if DEVELOPMENT:
    NAME = 'MST3K-Unstable'
    PREFIX = '/video/mst3kunstable'
    HTTP.CacheTime = 0  
    ICON = 'icon-dev.png'
else:
    NAME = 'MST3K'
    PREFIX = '/video/mst3k'
    ICON = 'icon-default.png'



ART = 'art-default.jpg'
THUMB_VC = 'icon-clip.jpg'
BASE_URL = 'http://www.club-mst3k.com'
EPISODES_URL = 'http://www.club-mst3k.com/episodes'
RE_YOUTUBEVIDEO = '[a-zA-Z0-9_-]*$'
YT_CLEANUPSTR = "youtube.com/embed/"
MAX_VIDEOS = 4 # For avoiding PMS timeout
FULL_CATEGORIES = [
    {'category_id': 'full', 'title': 'Full Episode'}
]
EXTRA_CATEGORIES = [
    {'category_id': 'best', 'title': 'Best Of'},
    {'category_id': 'short', 'title': 'Short'},
    {'category_id': 'original', 'title': 'Original Movie'}
]
CLIPTYPE = ["Full Episode", "Extras"]
ARTCLIP_LIST = [ "icon-clip1.jpg", "icon-clip2.jpg","icon-clip3.jpg",
                   "icon-clip4.jpg", "icon-clip5.jpg","icon-clip6.jpg",
                   "icon-clip7.jpg", "icon-clip8.jpg", "icon-clip9.jpg"
]

####################################################################################################
def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    NextPageObject.thumb = R(ICON)
    VideoClipObject.thumb = R(ICON)
    random.seed()

####################################################################################################
@handler(PREFIX, NAME, art=ART, thumb=ICON)
def MainMenu():
    oc = ObjectContainer()
    html = HTML.ElementFromURL(BASE_URL)

    # Create Seasons Dir
    for item in html.xpath('//th'):
        season_num = item.xpath('text()')[0].split('Season ')[-1]
        oc.add(
            DirectoryObject(
                key = Callback(EpisodesDir, season=season_num),
                title = 'Season ' + season_num
            )
        )

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no Seasons to list')
    else:
        return oc

####################################################################################################
@route(PREFIX + '/episodesdir')
def EpisodesDir(season):
    oc = ObjectContainer(title2 = 'Season ' + season)

    random.shuffle(ARTCLIP_LIST)
    # Create Episodes Dir
    # Current root: //body/div/div/table//tr/*
    try:
        iCurSeason = int(season)
        if iCurSeason == 0:
            html = HTML.ElementFromURL(EPISODES_URL).xpath('//body/div/div/table//tr[contains(@class,"season0")]/td//a[contains(@href,"/episodes/")]')
            if len(html) < 1: break

            for item in html:
                currTitle = item.xpath('./text()')[0]
                url = BASE_URL + item.xpath('./@href')[0]

                oc.add(
                    DirectoryObject(
                        key = Callback(EpisodeSubDir, season=season, title=currTitle, url=url ),
                        title = currTitle
                    )
                )
        elif iCurSeason < 11:
            html = HTML.ElementFromURL(EPISODES_URL).xpath('//body/div/div/table//tr/td//a[contains(@href,"/episodes/")]')
            if len(html) < 1: break

            for item in html:
                currTitle = item.xpath('./text()')[0]
                patternstr = '^%s\\d{2} - ' % (str(iCurSeason))
                match = Regex(patternstr, Regex.IGNORECASE).search(currTitle)
                if not match: continue
                url = BASE_URL + item.xpath('./@href')[0]

                oc.add(
                    DirectoryObject(
                        key = Callback(EpisodeSubDir, season=season, title=currTitle, url=url ),
                        title = currTitle
                    )
                )
        else:
            pass
    except:
        pass

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no Episodes to list')
    else:
        return oc

####################################################################################################
@route(PREFIX + '/episodesubdir')
def EpisodeSubDir(season, title, url):
    oc = ObjectContainer(title2=title)

    for num, name in enumerate(CLIPTYPE, start=0):
        oc.add(
            DirectoryObject(
                key = Callback(EpisodeVideos, season=season, title=title, url=url, clipType=num),
                title = name
            )
        )

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no Episodes to list')
    else:
        return oc

####################################################################################################
@route(PREFIX + '/episodevideos')
def EpisodeVideos(season, title, url, clipType):
    if int(clipType) == 0:
       currCategories = list(FULL_CATEGORIES)
       oc = ObjectContainer(title2=CLIPTYPE[0])
    else:
       currCategories = list(EXTRA_CATEGORIES)
       oc = ObjectContainer(title2=CLIPTYPE[1])

    if not url:
        Log.Debug(('EMPTY url in EpisodeVideos for: %s') % title)
        return ObjectContainer(header='Empty', message='Defective Episode url')

    # Videos

    currIndex = 1
    for category in currCategories:
        if currIndex > MAX_VIDEOS: break
        try:
            # Current root: //body/div/div/table//tr/*
            # Host site typo tolerant (*) xpath: //table[@class="link_bar"]//tr//*[@class="short"]
            xpathstr = (('//table[@class="link_bar"]//tr/td[@class="%s"]/following-sibling::td/div') % (category['category_id']))
            Log.Debug(('%s -> xpathstr #1: %s') % (category['category_id'], xpathstr))

            try:
                html = HTML.ElementFromURL(url).xpath(xpathstr)
                if len(html) < 1:
                    Log.Debug(('EMPTY html object for vid cat of %s') % (category['category_id']))
                    continue
            except:
                Log.Debug(('EXCEPTION: thrown getting "html" object for vid cat = %s') % (category['category_id']))
                continue

            videoList = list()
            for item in html:
                currVideoID = item.xpath('./a/@id')[0]
                Log.Debug(('%s - currVideoID: %s') % (category['category_id'], currVideoID))
                videoList.append(currVideoID)

            for videoItem in videoList:
                if currIndex > MAX_VIDEOS: break
                # Get video url
                # Eg //div[@id="link_1152"]/p/iframe
                xpathstr = '//div[@id="link_%s"]/p/iframe/@src' % (videoItem)
                try:
                    Log.Debug(('%s -> (Website) url: %s') % (category['category_id'], url))
                    Log.Debug(('%s -> xpathstr #2: %s') % (category['category_id'], xpathstr))
                    currUrl = HTML.ElementFromURL(url).xpath(xpathstr)[0]
                    # Eg currUrl = HTML.ElementFromURL(url).xpath('//div[@id="link_1152"]/p/iframe/@src')[0]
                    if not currUrl:
                        Log.Debug(('%s -> (Video) url [currUrl]: [NULL/FALSE]') % (category['category_id']))
                        continue
                    # Clean up YouTube urls (thus removing task from timeout "challenged" Plex Server)
                    if YT_CLEANUPSTR in currUrl:
                        Log.Debug(('YouTube 1: url clean-up search underway: currUrl = %s') % (currUrl))
                        match = Regex(RE_YOUTUBEVIDEO, Regex.IGNORECASE).search(currUrl)
                        Log.Debug(('YouTube 2: url clean-up matched: match = %s') % (match.group()))
                        if match:
                            currUrl = ('https://www.youtube.com/watch?v=%s') % (match.group())
                            Log.Debug(('YouTube 3: Final url = %s') % (currUrl))

                    Log.Debug(('%s -> (Video) url [currUrl]: %s') % (category['category_id'], currUrl))
                except:
                    Log.Debug(('EXCEPTION: vid cat = %s -> thrown getting current video url') % (category['category_id']))
                    continue
                try:
                    oc.add(
                        VideoClipObject(
                            url = currUrl,
                            title = '%s: %s [Link %d - sometimes broken]' % (title, category['title'], currIndex),
                            summary = 'Source:  %s' % (currUrl),
                            thumb = R(ARTCLIP_LIST[currIndex])
                        )
                    )

                    currIndex += 1
                except:
                    Log('EXCEPTION: thrown adding VideoClipObject Object')
                    continue
        except:
            pass

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no Videos to list')
    else:
        return oc
####################################################################################################
