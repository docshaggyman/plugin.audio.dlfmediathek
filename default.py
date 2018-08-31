# https://docs.python.org/2.7/
import os
import sys
import urllib
import urlparse
import datetime
# http://mirrors.kodi.tv/docs/python-docs/
import xbmcaddon
import xbmcgui
import xbmcplugin
# http://docs.python-requests.org/en/latest/
import requests
# https://docs.python.org/2/library/xml.etree.elementtree.html
import xml.etree.ElementTree as ET

def build_url(query):
    # build request URL
    base_url = sys.argv[0]
    return base_url + '?' + urllib.urlencode(query)

def get_page(url):
    # send request and return XML response
    return requests.get(url).text
    
def parse_page_content(page):
    # parse content from response XML
    root = ET.fromstring(page.encode('utf-8'))
    songs = {}
    index = 1
    
    for child in root:
        channelid = child[3].text.encode('utf-8')
        try:
            program = child[4].text.encode('utf-8')
            header = '{}: {}'.format(channelnames[channelid], program)
        except:
            header = channelnames[channelid]
        starttime = child[0].text.encode('utf-8')            
        episode = child[1].text.encode('utf-8') 
        songs.update({index: {'album_cover': channelicons[channelid], 'title': '[{}] - {} [{}]'.format(header, episode, starttime), 'url': child.attrib['url']}})
        index += 1
    return songs

def parse_page_programs(page):
    root = ET.fromstring(page.encode('utf-8'))
    programs = {}
    index = 1
    for child in root:
        programs.update({index: {'name': child.text.encode('utf-8'), 'id': child.get('id')}})
        index += 1
    return programs

def request_content(url):
    page = get_page(url)
    content = parse_page_content(page)
    build_song_list(content)

def request_program_list(url):
    page = get_page(url)
    programs = parse_page_programs(page)
    return programs

def build_search():
    dialog = xbmcgui.Dialog()
    searchterm = dialog.input('Enter search term', type=xbmcgui.INPUT_ALPHANUM)
    url = 'https://srv.deutschlandradio.de/aodlistaudio.1706.de.rpc?drau:searchterm={}&drau:page=1&drau:limit=50'.format(searchterm)
    request_content(url)

def build_livestreams():
    songs = {}
    index = 1

    for channel in channels:
        url = build_url({'mode': 'stream', 'url': liveurls[channel], 'title': '{} - Livestream'.format(channelnames[channel])})
        songs.update({index: {'album_cover': channelicons[channel], 'title': '{} - Livestream'.format(channelnames[channel]), 'url': url}})
        index += 1
    build_song_list(songs)

def build_programs_main():
    url = build_url({'mode': 'folder', 'foldername': 'all_programs'})
    li = xbmcgui.ListItem('Alle Sendungen', iconImage=channelicons['DLR'])
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    for channel in channels:
        url = build_url({'mode': 'folder', 'foldername': '{}_programs'.format(channel)})
        li = xbmcgui.ListItem('{} - Sendungen'.format(channelnames[channel]), iconImage=channelicons[channel])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

def build_programs_sub(programs):
    for program in programs:
        url = build_url({'mode': 'folder', 'foldername': 'program_id_{}'.format(programs[program]['id'])})
        li = xbmcgui.ListItem(programs[program]['name'], iconImage=channelicons['DLR'])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

def build_today():
    for channel in channels:
        url = build_url({'mode': 'folder', 'foldername': '{}_today'.format(channel)})
        li = xbmcgui.ListItem('{} - Heute'.format(channelnames[channel]), iconImage=channelicons[channel])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)
    
def build_song_list(songs):
    song_list = []
    # iterate over the contents of the dictionary songs to build the list
    for song in songs:
        # create a list item using the song filename for the label
        li = xbmcgui.ListItem(label=songs[song]['title'], thumbnailImage=songs[song]['album_cover'])
        # set the fanart to the albumc cover
        li.setProperty('fanart_image', songs[song]['album_cover'])
        # set the list item to playable
        li.setProperty('IsPlayable', 'true')
        # build the plugin url for Kodi
        # Example: plugin://plugin.audio.example/?url=http%3A%2F%2Fwww.theaudiodb.com%2Ftestfiles%2F01-pablo_perez-your_ad_here.mp3&mode=stream&title=01-pablo_perez-your_ad_here.mp3
        url = build_url({'mode': 'stream', 'url': songs[song]['url'], 'title': songs[song]['title']})
        # add the current list item to a list
        song_list.append((url, li, False))
    # add list to Kodi per Martijn
    # http://forum.kodi.tv/showthread.php?tid=209948&pid=2094170#pid2094170
    xbmcplugin.addDirectoryItems(addon_handle, song_list, len(song_list))
    # set the content of the directory
    xbmcplugin.setContent(addon_handle, 'audio')
    xbmcplugin.endOfDirectory(addon_handle)
    
def play_song(url):
    # set the path of the song to a list item
    play_item = xbmcgui.ListItem(path=url)
    # the list item is ready to be played by Kodi
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    
def main():
    global channels, channelnumbers, channelnames, channelicons, liveurls
    iconroot = os.path.join(os.path.dirname(__file__),'resources', 'media')
    channels = ["DLF", "DRW", "DRK"]
    channelnumbers = {'DLF' : '4', 'DRW' : '1', 'DRK': '3'}
    channelnames = {'DLF' : 'Deutschlandfunk', 'DRW' : 'Deutschlandfunk Nova', 'DRK' : 'Deutschlandfunk Kultur', }
    channelicons = {'DLF' : os.path.join(iconroot, 'dlf.png'), 'DRW':os.path.join(iconroot, 'dlfnova.png'), 'DRK':os.path.join(iconroot, 'dlfkultur.png'), 'DLR': os.path.join(iconroot, 'dlr.png')}
    liveurls = {'DLF' : 'http://st01.dlf.de/dlf/01/128/mp3/stream.mp3', 'DRW':'http://st03.dlf.de/dlf/03/128/mp3/stream.mp3', 'DRK':'http://st02.dlf.de/dlf/02/128/mp3/stream.mp3'}

    args = urlparse.parse_qs(sys.argv[2][1:])
    mode = args.get('mode', None)
    
    # initial launch of add-on
    if mode is None:
        url = build_url({'mode': 'folder', 'foldername': 'Livestream'})
        li = xbmcgui.ListItem('Livestream', iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

        url = build_url({'mode': 'folder', 'foldername': 'Heutiges Programm'})
        li = xbmcgui.ListItem('Heutiges Programm', iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

        url = build_url({'mode': 'folder', 'foldername': 'Sendungen'})
        li = xbmcgui.ListItem('Sendungen', iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

        url = build_url({'mode': 'folder', 'foldername': 'Suche'})
        li = xbmcgui.ListItem('Suche', iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)
    # A menu item has been selected
    elif mode[0] == 'folder':
        foldername = args['foldername'][0]

        if foldername == 'Suche': # Main menu: Search
            build_search()
        elif foldername == 'Sendungen': # Main menu: Programs
            build_programs_main()
        elif foldername == 'Livestream': # Main menu: Livestream
            build_livestreams()
        elif foldername == 'Heutiges Programm': # Main menu: Today's programme
            build_today()
        elif foldername in ['{}_today'.format(channel) for channel in channels]: # Today's programme: Channel selection
            now = datetime.datetime.now()
            today = now.strftime("%d.%m.%Y")
            channel = foldername[:-6]
            url = 'https://srv.deutschlandradio.de/aodlistaudio.1706.de.rpc?drau:station_id={0}&drau:from={1}&drau:to={1}&drau:page=1&drau:limit=50'.format(channelnumbers[channel],today)
            request_content(url)
        elif foldername in ['{}_programs'.format(channel) for channel in channels] or foldername == 'all_programs': # Programs: Channel selection
            channel = foldername[:-9]
            if foldername == 'all_programs':
                url = 'https://srv.deutschlandradio.de/aodlistbroadcasts.1707.de.rpc' ## selection "all channels"
            else:
                url = 'https://srv.deutschlandradio.de/aodlistbroadcasts.1707.de.rpc?drbm:station_id={}'.format(channelnumbers[channel]) ## specific channel selected
            programs = request_program_list(url)
            build_programs_sub(programs)
        elif foldername[:11] == 'program_id_': # Programs: Program selection
            program_id = foldername[11:]
            url = 'https://srv.deutschlandradio.de/aodlistaudio.1706.de.rpc?drau:broadcast_id={}&drau:page=1&drau:limit=30'.format(program_id)
            request_content(url)
            
            
    # A song from the list has been selected
    elif mode[0] == 'stream':
        # pass the url of the song to play_song
        play_song(args['url'][0])
    
if __name__ == '__main__':
    addon_handle = int(sys.argv[1])
    main()