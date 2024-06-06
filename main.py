# -*- coding:utf-8 -*-
import os
import re
import sys
import json
import base64
import datetime
import urllib.parse
import requests
import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import xbmcplugin

# plugin info
ADDON_name = '哆啦搜索'
ADDON_handle = int(sys.argv[1])  # 当前插件句柄
ADDON_address = sys.argv[0]  # 当前插件地址
ADDON_parm = sys.argv[2]  # 问号以后的内容
ADDON_dialog = xbmcgui.Dialog()
ADDON_PlayerStyle = int(xbmcplugin.getSetting(ADDON_handle, 'Duola_play_style'))
ADDON_PlayerMimes = ['.m3u8', '.mp4', '.flv', '.ts', '.ogg', '.mp3']

# Get addon base path
ADDON_path = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
ICONS_dir = os.path.join(ADDON_path, 'resources', 'images', 'icons')
FANART_dir = os.path.join(ADDON_path, 'resources', 'images', 'fanart')

# Demo api: https://raw.githubusercontent.com/malimaliao/kodi/matrix/api/plugin.video.duolasousuo/v1.json
ADDON_api = 'https://gitee.com/beijifeng/kodi/raw/matrix/api/plugin.video.duolasousuo/v1.json'

# bot config
UA_timeout = 30
UA_head = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36',
}

# global debug
print('duola_debug: [' + str(ADDON_handle) + ']' + ADDON_address + ' || ' + ADDON_parm)


# custom function
def check_json(input_str):
    try:
        json.loads(input_str)
        return True
    except:
        return False


def check_url_mime(url):
    hz = '.' + url.split('.')[-1]
    if hz in ADDON_PlayerMimes:
        return True
    else:
        return False


def remove_html_tags(html):
    dr = re.compile(r'<[^>]+>', re.S)
    text = dr.sub('', html)
    return text


# request: https://123.com/api/provide/vod/?wd={keyword}
# return: 
def Web_load_search(url, keyword):
    get_url = url + '?wd=' + keyword
    try:
        res = requests.get(url=get_url, headers=UA_head, timeout=UA_timeout)
        res_text = res.text
        # print('duola_debug:'+get_url, res.text)
        # ADDON_dialog.ok(ADDON_name + 'debug', get_url)
    except requests.exceptions.RequestException as e:
        res_text = ''
        ADDON_dialog.notification(heading=ADDON_name, message='搜索获取失败，暂不可用', time=3000)
        print('duola_debug: Web_load_search => bad', e)
    if check_json(res_text):
        res_json = json.loads(res_text)
        if res_json['code'] == 1:
            if len(res_json['list']) > 0:
                for video in res_json['list']:
                    vod_id = str(video['vod_id'])
                    vod_name = video['vod_name']
                    vod_remarks = video['vod_remarks']
                    vod_year = str(video['vod_year'])
                    # 建立kodi菜单
                    list_item = xbmcgui.ListItem(vod_name + ' (' + vod_year + ') [COLOR yellow]' + vod_remarks + '[/COLOR]')
                    list_item.setArt({'icon': os.path.join(ICONS_dir, 'video.png')})
                    a_url = urllib.parse.quote(url)
                    xbmcplugin.addDirectoryItem(ADDON_handle, ADDON_address + '?Bot_search_return=' + a_url + '&read_detail=' + vod_id, list_item, True)
                # 退出kodi菜单布局
                xbmcplugin.endOfDirectory(handle=ADDON_handle, succeeded=True, updateListing=False, cacheToDisc=True)
            else:
                print('duola_debug:找不到资源')
                ADDON_dialog.notification(heading=ADDON_name, message='抱歉，找不到相关资源', time=3000)
        else:
            print('duola_debug:无法解析json')
            ADDON_dialog.notification(heading=ADDON_name, message='抱歉，由于无法解析返回的数据，服务暂时不可用，请稍后重试', time=3000)
    else:
        print('duola_debug:目标服务器返回的数据无法解析')
        ADDON_dialog.notification(heading=ADDON_name, message='抱歉，目标服务器返回的数据无法响应，服务暂不可用', time=3000)


# request: https://123.com/api/provide/vod/?ac=detail&ids={detail_id}
# return: play list
def Web_load_detail_one(url, detail_id):
    get_url = url + '?ac=detail&ids=' + detail_id
    try:
        res = requests.get(url=get_url, headers=UA_head, timeout=UA_timeout)
        res_text = res.text
        # print('duola_debug:'+get_url, res.text)
    except requests.exceptions.RequestException as e:
        res_text = ''
        ADDON_dialog.notification(heading=ADDON_name, message='内容获取失败，暂不可用', time=3000)
        print('duola_debug: Web_load_detail_one => bad', e)
    if check_json(res_text):
        res_json = json.loads(res_text)
        if res_json['code'] == 1:
            if len(res_json['list']) > 0:
                video = res_json['list'][0]  # 仅提取一个
                v_id = str(video['vod_id'])
                v_name = video['vod_name']
                v_typename = video['type_name']
                v_picture = video['vod_pic']
                v_list_text = video['vod_play_url']  # 多地址合集
                v_infos = {}
                try:
                    v_infos['title'] = video['vod_name']
                    v_infos['originaltitle'] = video['vod_sub']
                    v_infos['sorttitle'] = video['vod_en']
                    v_infos['country'] = video['vod_area'].split(",")
                    v_infos['year'] = video['vod_year']
                    v_infos['director'] = video['vod_director']
                    v_infos['writer'] = video['vod_writer'].split(",")
                    v_infos['cast'] = video['vod_actor'].split(',')
                    v_infos['plotoutline'] = video['vod_blurb']
                    v_infos['plot'] = remove_html_tags(video['vod_content'])
                    v_infos['rating'] = float(video['vod_douban_score'])
                except IndexError as e:
                    pass
                # dialog.select
                V_name_list = []
                V_m3u8_list = []
                playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                # 按$$$分隔不同的[播放来源]数据
                # 01集$http://a.com/1.mp4#02集$http://a.com/2.mp4$$$01集$http://a.com/1.flv#02集$http://a.com/2.flv
                V_class_data = v_list_text.split('$$$')
                if len(V_class_data) > 0:
                    select_title = '请选择播放源开始播放【' + v_name + '】'
                    for V_list in V_class_data:
                        # 按#分隔相同的[播放来源]数据中的不同[播放地址/剧集]
                        # 第01集$http://abc.com/1.flv#第02集$http://abc.com/2.flv
                        V_playlist = V_list.split('#')
                        V_i = 0
                        for V_play in V_playlist:
                            # 按#分隔，将vod_title与vod_url区分
                            # 第01集$http://abc.com/1.flv
                            V = V_play.split('$')
                            if len(V) == 2 and check_url_mime(V[1].strip()):
                                _v_play_label = V[0].strip()  # 去除首尾空格
                                _v_play_url = V[1].strip()  # 去除首尾空格
                                V_name_list.append(_v_play_label)  # 播放标签
                                V_m3u8_list.append(_v_play_url)  # 播放地址
                                # listitem for player_style 2
                                list_item = xbmcgui.ListItem(v_name + ': ' + _v_play_label, v_typename)
                                list_item.setArt({'thumb': v_picture, 'poster': v_picture})
                                list_item.setInfo('video', v_infos)
                                playlist.add(url=_v_play_url, listitem=list_item, index=V_i)
                                V_i = V_i + 1
                            else:
                                pass  # 不符合条件的播放地址跳过
                else:
                    select_title = '此视频暂时没有播放源'
                # 播放方式
                print('duola_debug: ADDON_PlayerStyle@' + str(ADDON_PlayerStyle))
                # player_style -------------------------------------------------
                if ADDON_PlayerStyle == 0:
                    a = -1
                    for x in V_name_list:
                        a = a + 1
                        list_item = xbmcgui.ListItem('[COLOR blue]【播放】[/COLOR]' + v_name + ' (' + x + ')')
                        list_item.setArt({'icon': os.path.join(ICONS_dir, 'play.png'), 'poster': v_picture})
                        list_item.setInfo('video', v_infos)
                        xbmcplugin.addDirectoryItem(ADDON_handle, V_m3u8_list[a], list_item, False)
                    xbmcplugin.endOfDirectory(handle=ADDON_handle, succeeded=True, updateListing=False, cacheToDisc=True)
                # player_style -------------------------------------------------
                if ADDON_PlayerStyle == 1:
                    dialog = xbmcgui.Dialog()
                    select_i = dialog.select(select_title, V_name_list)
                    print('duola_debug: select_i ' + str(select_i))
                    if select_i >= 0:
                        list_item = xbmcgui.ListItem(v_name, v_typename, V_m3u8_list[select_i], offscreen=False)
                        list_item.setArt({'thumb': v_picture, 'poster': v_picture})
                        list_item.setInfo('video', v_infos)
                        # ADDON_dialog.info(list_item)  # 弹出视频
                        xbmc.Player().play(item=V_m3u8_list[select_i], listitem=list_item)
                        ADDON_dialog.notification(heading=ADDON_name, message='视频即将播放，请耐心稍候一会', time=6000, sound=False)
                    xbmcplugin.endOfDirectory(handle=ADDON_handle, succeeded=True, updateListing=False, cacheToDisc=True)
                # player_style -------------------------------------------------
                if ADDON_PlayerStyle == 2:
                    dialog = xbmcgui.Dialog()
                    select_i = dialog.select(select_title, V_name_list)
                    print('duola_debug: select_i ' + str(select_i))
                    if select_i >= 0:
                        list_item = xbmcgui.ListItem(v_name, v_typename, V_m3u8_list[select_i], offscreen=False)
                        list_item.setArt({'thumb': v_picture, 'poster': v_picture})
                        list_item.setInfo('video', v_infos)
                        xbmc.Player().play(item=playlist, listitem=list_item, windowed=False, startpos=select_i)
                        ADDON_dialog.notification(heading=ADDON_name, message='视频即将播放，请耐心稍候一会', time=6000, sound=False)
                        xbmcplugin.endOfDirectory(handle=ADDON_handle, succeeded=True, updateListing=False, cacheToDisc=True)
            else:
                print('duola_debug:没有数据')
                ADDON_dialog.notification(heading=ADDON_name, message='抱歉，找不到播放列表', time=3000)
        else:
            print('duola_debug:无法解析json')
            ADDON_dialog.notification(heading=ADDON_name, message='抱歉，由于无法解析返回的数据，服务暂时不可用，请稍后重试', time=3000)
    else:
        print('duola_debug:目标服务器返回的数据无法解析')
        ADDON_dialog.notification(heading=ADDON_name, message='抱歉，目标服务器返回的数据无法响应，服务暂不可用', time=3000)


# request: https://123.com/api/provide/vod/?ac=list
# return: channels list
def Web_load_channels(url):
    get_url = url + '?ac=list'
    try:
        res = requests.get(url=get_url, headers=UA_head, timeout=UA_timeout)
        res_text = res.text
    except requests.exceptions.RequestException as e:
        res_text = ''
        ADDON_dialog.notification(heading=ADDON_name, message='栏目获取失败，暂不可用', time=3000)
        print('duola_debug: Web_load_channels => bad', e)
    if check_json(res_text):
        res_json = json.loads(res_text)
        if res_json['code'] == 1:
            if len(res_json['class']) > 0:
                for channel in res_json['class']:
                    type_id = str(channel['type_id'])
                    type_name = channel['type_name']
                    '''
                    type_pid = str(channel['type_pid'])
                    if type_pid != '0':
                        list_item = xbmcgui.ListItem(type_name)
                        a_url = urllib.parse.quote(url)
                        xbmcplugin.addDirectoryItem(
                        ADDON_handle, 
                        ADDON_address + '?Bot_channel=' + a_url + '&channel_id='+type_id, list_item,
                        True
                        )
                    '''
                    list_item = xbmcgui.ListItem(type_name)
                    a_url = urllib.parse.quote(url)
                    xbmcplugin.addDirectoryItem(ADDON_handle, ADDON_address + '?Bot_channel=' + a_url + '&channel_id=' + type_id, list_item, True)
                xbmcplugin.endOfDirectory(handle=ADDON_handle, succeeded=True, updateListing=False, cacheToDisc=True)
            else:
                print('duola_debug:暂无栏目')
                ADDON_dialog.notification(heading=ADDON_name, message='当前引擎暂无栏目', time=3000)
        else:
            print('duola_debug:栏目暂时无法获取')
            ADDON_dialog.notification(heading=ADDON_name, message='当前引擎栏目暂时无法获取', time=3000)
    else:
        print('duola_debug:无法解析json')
        ADDON_dialog.notification(heading=ADDON_name, message='无法解析数据，服务暂时不可用，请稍后重试', time=3000)


# request: https://123.com/api/provide/vod/?ac=videolist&t={type_id}&pg={page}
# return: list list
def Web_load_list(url, type_id, page):
    get_url = url + '?ac=videolist&t=' + type_id + '&pg=' + page
    print('duola_debug: load ' + get_url)
    try:
        res = requests.get(url=get_url, headers=UA_head, timeout=UA_timeout)
        res_text = res.text
    except requests.exceptions.RequestException as e:
        res_text = ''
        ADDON_dialog.notification(heading=ADDON_name, message='列表获取失败，暂不可用', time=3000)
        print('duola_debug: Web_load_list => bad', e)
    if check_json(res_text):
        res_json = json.loads(res_text)
        if res_json['code'] == 1:
            if len(res_json['list']) > 0:
                xbmcplugin.setContent(ADDON_handle, 'tvshows')  # 内容类型
                # 生成列表
                for video in res_json['list']:
                    vod_id = str(video['vod_id'])
                    vod_name = video['vod_name']
                    vod_remarks = video['vod_remarks']
                    vod_typename = video['type_name']
                    vod_pic = video['vod_pic']
                    v_infos = {}
                    try:
                        v_infos['title'] = video['vod_name']
                        v_infos['originaltitle'] = video['vod_sub']
                        v_infos['sorttitle'] = video['vod_en']
                        v_infos['tag'] = video['vod_remarks']
                        v_infos['country'] = video['vod_area']
                        v_infos['year'] = video['vod_year']
                        v_infos['director'] = video['vod_director']
                        v_infos['writer'] = video['vod_writer'].split(",")
                        v_infos['cast'] = video['vod_actor'].split(',')
                        v_infos['plotoutline'] = video['vod_blurb']
                        v_infos['plot'] = remove_html_tags(video['vod_content'])
                        v_infos['rating'] = float(video['vod_score'])
                    except IndexError as e:
                        pass
                    # 菜单构建+1
                    list_item = xbmcgui.ListItem(vod_name + ' [COLOR=blue]' + vod_remarks + '[/COLOR]')
                    list_item.setArt({'icon': os.path.join(ICONS_dir, 'video.png'), 'poster': vod_pic})
                    list_item.setInfo('video', v_infos)
                    a_url = urllib.parse.quote(url)
                    xbmcplugin.addDirectoryItem(ADDON_handle, ADDON_address + '?Bot_search_return=' + a_url + '&read_detail=' + vod_id, list_item, True)
                page = str(int(page) + 1)
                list_item = xbmcgui.ListItem('[COLOR yellow]下一页[/COLOR]([COLOR blue]' + str(res_json['page']) + '[/COLOR]/' + str(res_json['pagecount']) + ')')
                xbmcplugin.addDirectoryItem(ADDON_handle, ADDON_address + '?Bot_page=' + url + '&channel_id=' + type_id + '&page_id=' + page, list_item, True)
                # kodi 菜单构造完毕
                xbmcplugin.endOfDirectory(handle=ADDON_handle, succeeded=True, updateListing=False, cacheToDisc=True)
            else:
                print('duola_debug:暂无列表')
                ADDON_dialog.notification(heading=ADDON_name, message='当前栏目下列表是空的，请稍后重试', time=3000)
        else:
            print('duola_debug:列表暂时无法获取')
            ADDON_dialog.notification(heading=ADDON_name, message='当前栏目下节目列表暂时无法获取', time=3000)
    else:
        print('duola_debug:无法解析json')
        ADDON_dialog.notification(heading=ADDON_name, message='抱歉，无法解析返回的数据，服务暂时不可用，请稍后重试', time=3000)


# API->engine get new
def API_get_Cloud_Engine_new(Cache_save_path):
    print('duola_debug: API_get_Cloud_Engine_new', ADDON_api)
    try:
        res = requests.get(url=ADDON_api, headers=UA_head, timeout=UA_timeout)
        cloud_engine_text = res.text
        # 写入缓存，降低服务器请求数
        expires_in = 3600  # 初始有效时间为1小时
        if check_json(cloud_engine_text):
            api_json = json.loads(cloud_engine_text)
            notice = base64.b64decode(api_json['notice'])
            client = str(api_json['client'])
            if notice != "":
                ADDON_dialog.notification(heading=ADDON_name + ' 最新版本: ' + client, message=notice, time=4000)
            if 'expires_in' in api_json:
                expires_in = float(api_json['expires_in'])  # 使用服务器限定的有效期
            next_time = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)  # 设定时间有效期在n秒后失效
            next_timestamp = str(int(next_time.timestamp()))
            with xbmcvfs.File(Cache_save_path, 'w') as f:
                time_value = 'next_timestamp=' + next_timestamp  # 有效时间
                f.write(time_value)  # time
                f.write('\n--------\n')  # 此处分隔符
                f.write(cloud_engine_text)  # json
    except requests.exceptions.RequestException as e:
        cloud_engine_text = ''
        print('duola_debug: API_get_Cloud_Engine_new => BAD', e)
    return cloud_engine_text


# API->engine get
def API_get_Cloud_Engine():
    print('duola_debug: API_get_Cloud_Engine')
    temp_path = xbmcvfs.translatePath('special://home/temp')
    my_addon = xbmcaddon.Addon()
    my_addon_id = my_addon.getAddonInfo('id')
    my_cache_path = os.path.join(temp_path, my_addon_id, '')
    xbmcvfs.mkdirs(my_cache_path)
    if xbmcvfs.exists(my_cache_path):
        print('duola_debug: Cache directory read successfully ->' + my_cache_path)
        my_cloud_engine_cache = os.path.join(my_cache_path, 'Duola_Local_Search_Engine.txt')
        if xbmcvfs.exists(my_cloud_engine_cache):
            cloud_engine_text = ""
            with xbmcvfs.File(my_cloud_engine_cache) as f:
                cache = f.read()
                a = cache.split('--------')
                a101 = a[1]  # json text
                b = a[0].split('timestamp=')
                cc = b[1].replace('\n', '')  # next_timestamp=1640507115
                print(b, cc)
                next_timestamp = int(cc)
                this_timestamp = int(datetime.datetime.now().timestamp())
                print('this_time:' + str(this_timestamp) + ',next_time:' + str(next_timestamp), cloud_engine_text)
                if this_timestamp < next_timestamp:
                    print('duola_debug: effective cache, read local ->' + my_cloud_engine_cache)
                    cloud_engine_text = a101
                else:
                    print('duola_debug: cache invalidation, download again')
                    cloud_engine_text = API_get_Cloud_Engine_new(my_cloud_engine_cache)
        else:
            print('duola_debug: First cloud download of data')
            cloud_engine_text = API_get_Cloud_Engine_new(my_cloud_engine_cache)
        # ----- 解析json ------
        if check_json(cloud_engine_text):
            api = json.loads(cloud_engine_text)
            # print('duola_debug:zy code' + str(api['code'] ))
            # print('duola_debug:zy data_list' + str(len(api['data']['list'])) )
            if api['code'] == 1 and len(api['data']['list']) > 0:
                print('duola_debug:zy YES')
                for zy in api['data']['list']:
                    # print('duola_debug:zy' + zy['name'] + '@' + zy['api_url'])
                    if zy['status'] == 1:
                        _api_url = urllib.parse.quote(base64.b64decode(zy['api_url']))  # base64 解码后，再URL编码
                        _api_title = ' [COLOR blue] (' + zy['name'] + ') [/COLOR]'
                        item_cloud = xbmcgui.ListItem('哆啦搜索' + _api_title)
                        item_cloud.setArt({'icon': os.path.join(ICONS_dir, 's2.png')})
                        xbmcplugin.addDirectoryItem(ADDON_handle, ADDON_address + '?Bot_engine=' + _api_url, item_cloud, True)
                    else:
                        _api_title = ' [COLOR yellow] (' + zy['name'] + ') ' + ' 暂不可用[/COLOR]'
                        item_cloud = xbmcgui.ListItem('哆啦搜索' + _api_title)
                        item_cloud.setArt({'icon': os.path.join(ICONS_dir, 's0.png')})
                        xbmcplugin.addDirectoryItem(ADDON_handle, ADDON_address, item_cloud, True)
            else:
                ADDON_dialog.notification(heading=ADDON_name, message='云端搜索引擎暂时故障,请稍后重试' + api['message'], time=3000)
        else:
            ADDON_dialog.notification(heading=ADDON_name, message='暂时无法获取云端搜索引擎列表,请稍后重试', time=3000)
        # ----- 解析json ------
    else:
        print('duola_debug: 缓存目录读取失败->' + my_cache_path)
        ADDON_dialog.ok(ADDON_name, '抱歉，由于缓存无法读写，因此云端引擎不可用。文件地址：' + my_cache_path)


# /
if ADDON_parm == '':
    print('duola_debug: load main')
    enable_cloud = xbmcplugin.getSetting(ADDON_handle, 'Duola_Cloud_Search_Engine')
    _b = ""
    # add cloud menu
    if enable_cloud == 'true':
        _b = ' (本机内置接口)'
        API_get_Cloud_Engine()
    # add local menu
    _local_api_url = xbmcplugin.getSetting(ADDON_handle, 'Duola_Local_Search_Engine')
    api_url = urllib.parse.quote(_local_api_url)
    item_engine = xbmcgui.ListItem('哆啦搜索' + _b)
    item_engine.setArt({'icon': os.path.join(ICONS_dir, 's1.png')})
    xbmcplugin.addDirectoryItem(ADDON_handle, ADDON_address + '?Bot_engine=' + api_url, item_engine, True)
    # add help menu
    item_engine = xbmcgui.ListItem('[COLOR=yellow]帮助&声明[/COLOR]')
    item_engine.setArt({'icon': os.path.join(ICONS_dir, 'doc.png')})
    xbmcplugin.addDirectoryItem(ADDON_handle, ADDON_address + '?Bot_help', item_engine, True)
    # exit menu build
    xbmcplugin.endOfDirectory(handle=ADDON_handle, succeeded=True, updateListing=False, cacheToDisc=True)

# /?Bot_help
if '?Bot_help' in ADDON_parm:
    help_text = '1, 搜索中文关键词时, 请确保已安装Kodi中文输入法\n'
    help_text += '2, 插件内置搜索接口允许自定义，可通过插件设置修改\n'
    help_text += '3, 插件内置云搜索引擎，可通过设置开启云端搜索列表\n'
    help_text += '4, 部分资源首次播放缓冲较慢，耐心等待后就会流畅\n'
    help_text += '\n插件声明：\n本插件是基于学习和研究目的通过爬虫技术所抓取的所有内容均来自于第三方网站的数据，插件不涉及资源存储或分发。'
    help_text += '作者不对其内容承担任何责任！仅供个人学习交流之用，24小时内请自觉卸载，勿作商业用途。'
    ADDON_dialog.ok(ADDON_name + ' 帮助&声明', help_text)

# /?Bot_engine=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F :: 云引擎
if '?Bot_engine=' in ADDON_parm:
    _parm_url = urllib.parse.unquote(ADDON_parm)
    engine_url = _parm_url.split("Bot_engine=")[1]
    item_menu = xbmcgui.ListItem('[COLOR=yellow]在线搜索[/COLOR]')
    item_menu.setArt({'icon': os.path.join(ICONS_dir, 'search.png')})
    xbmcplugin.addDirectoryItem(ADDON_handle, ADDON_address + '?Bot_search=' + engine_url, item_menu, True)
    Web_load_channels(engine_url)
    xbmcplugin.endOfDirectory(handle=ADDON_handle, succeeded=True, updateListing=False, cacheToDisc=True)

# /?Bot_search=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F
if '?Bot_search=' in ADDON_parm:
    _parm_url = urllib.parse.unquote(ADDON_parm)
    engine_url = _parm_url.split("Bot_search=")[1]
    keyboard = xbmc.Keyboard()
    keyboard.setHeading('请输入关键词')
    keyboard.doModal()
    # xbmc.sleep(1500)
    if keyboard.isConfirmed():
        keyword = keyboard.getText()
        if len(keyword) < 1:
            msgbox = ADDON_dialog.ok(ADDON_name, '您必须输入关键词才可以搜索相关内容')
    else:
        keyword = ''
    print('duola_debug:' + keyword)
    if len(keyword) > 0:
        Web_load_search(engine_url, keyword)

# /?Bot_channel=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F&channel_id=123
if '?Bot_channel=' in ADDON_parm and '&channel_id=' in ADDON_parm:
    _parm_url = urllib.parse.unquote(ADDON_parm)
    channel_id = _parm_url.split("&channel_id=")[1]
    engine_url = _parm_url.replace('&channel_id=' + channel_id, '').split("Bot_channel=")[1]
    print('duola_debug:', engine_url, channel_id)
    if channel_id != "":
        Web_load_list(engine_url, channel_id, '1')
    else:
        print('duola_debug:传入的 channel_id 地址为空')
        ADDON_dialog.notification(heading=ADDON_name, message='此栏目无效', time=3000)

# /?Bot_page=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F&channel_id=123&page_id=2
if '?Bot_page=' in ADDON_parm and '&channel_id=' in ADDON_parm and '&page_id=' in ADDON_parm:
    _parm_url = urllib.parse.unquote(ADDON_parm)
    page_number = _parm_url.split("&page_id=")[1]
    channel_id = _parm_url.replace('&page_id=' + page_number, '').split("&channel_id=")[1]
    engine_url = _parm_url.replace('&channel_id=' + channel_id + '&page_id=' + page_number, '').split("Bot_page=")[1]
    if channel_id != "":
        Web_load_list(engine_url, channel_id, page_number)
    else:
        print('duola_debug:传入的 channel_id 地址为空')
        ADDON_dialog.notification(heading=ADDON_name, message='此栏目无效', time=3000)

# /?Bot_search_return=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F&read_detail=123
if '?Bot_search_return=' in ADDON_parm and '&read_detail' in ADDON_parm:
    _parm_url = urllib.parse.unquote(ADDON_parm)
    detail_id = _parm_url.split("&read_detail=")[1]
    engine_url = _parm_url.replace('&read_detail=' + detail_id, '').split("Bot_search_return=")[1]
    print('duola_debug', engine_url, detail_id)
    if detail_id != "":
        this_list = Web_load_detail_one(engine_url, detail_id)
    else:
        print('duola_debug:传入的 read_detail 地址为空')
        ADDON_dialog.notification(heading=ADDON_name, message='此视频信息无效', time=3000)
