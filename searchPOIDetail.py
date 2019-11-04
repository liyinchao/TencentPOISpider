# _*_ coding:UTF-8 _*_
# 开发时间: 2019/10/31 21:42
# 文件名称: searchPOIDetail.py
# 开发人员: liaop
# 开发团队: sunyea
# 代码概述: 精细化搜索

import requests
import json
from urllib import parse
import time
from utility.Logger import getLogger


logger = getLogger('searchDetail')
stop = False


def get_keys(filename):
    '''
    获取key
    :return:
    '''
    keys = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            keys.append(line.replace('\n', ''))
    return keys


def get_rect(filename):
    '''
    获取rect
    :param filename:
    :return:
    '''
    rects = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            rects.append(json.loads(line))
    return rects


def get_category(filename):
    '''
    获取分类
    :param filename:
    :return:
    '''
    categories = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            arr_line = line.replace('\n', '').split(':')
            categories.append({'keywd': arr_line[0], 'category': arr_line[1]})
    return categories


def split_rect(rect):
    '''
    分解rect
    :param rect:
    :return:
    '''
    rects = []
    lat1 = rect.get('lat1')
    lng1 = rect.get('lng1')
    lat2 = rect.get('lat2')
    lng2 = rect.get('lng2')

    lat1_5 = lat1+(lat2-lat1)/2
    lng1_5 = lng1+(lng2-lng1)/2

    rects.append({'lat1': lat1, 'lng1': lng1, 'lat2': lat1_5, 'lng2': lng1_5})
    rects.append({'lat1': lat1_5, 'lng1': lng1, 'lat2': lat2, 'lng2': lng1_5})
    rects.append({'lat1': lat1, 'lng1': lng1_5, 'lat2': lat1_5, 'lng2': lng2})
    rects.append({'lat1': lat1_5, 'lng1': lng1_5, 'lat2': lat2, 'lng2': lng2})
    return rects


def search_one_page(rect, category, key, page):
    '''
    检索一页
    :param rect:
    :param category:
    :param key:
    :param page:
    :return:
    '''
    search_url = 'https://apis.map.qq.com/ws/place/v1/search?boundary=rectangle({rect})&' \
                 'keyword={keywd}{category}&page_size=20&page_index={page}&' \
                 'key={key}'
    parm = {}
    parm['rect'] = '{},{},{},{}'.format(rect.get('lat1'), rect.get('lng1'), rect.get('lat2'), rect.get('lng2'))
    parm['keywd'] = parse.quote(category.get('keywd'))
    parm['category'] = '&filter=category={}'.format(parse.quote(category.get('category')))
    parm['page'] = page
    parm['key'] = key
    url = search_url.format(**parm)
    response = requests.get(url)
    js = json.loads(response.content.decode())
    status = int(js.get('status'))
    if status == 0:
        total = int(js.get('count'))
        return 0, total, js.get('data', [])
    else:
        return status, 0, js.get('message')


def search_one_cate(index, rect, category, key):
    '''
    检索一条
    :param index:
    :param rect:
    :param category:
    :param key:
    :return:
    '''
    try:
        page = 1
        k = key[0]
        list_data = []
        while True:
            status, total, data = search_one_page(rect, category, k, page)
            if status == 120:
                time.sleep(0.1)
                logger.error('在检索第 {} 个矩形区域的 {} 类信息 key 超 时'.format(index, category.get('category')))
                continue
            if status == 121:
                logger.error('在检索第 {} 个矩形区域的 {} 类信息 key 超 量'.format(index, category.get('category')))
                key.pop(0)
                if len(key)>0:
                    k = key[0]
                    continue
                else:
                    logger.error('在检索第 {} 个矩形区域的 {} 类信息 key 已经用尽'.format(index, category.get('category')))
                    global stop
                    stop = True
                    break
            if status == 0:
                if total > 200:
                    logger.error('在检索第 {} 个矩形区域的 {} 类信息数量{}，分解矩形'.format(index, category.get('category'),
                                                                         total))
                    # logger.debug('分解矩形：{}'.format(rect))
                    rects = split_rect(rect)
                    lat_old = '{:.5f}'.format(rect.get('lat2'))
                    lng_old = '{:.5f}'.format(rect.get('lng2'))
                    lat_new = '{:.5f}'.format(rects[0].get('lat2'))
                    lng_new = '{:.5f}'.format(rects[0].get('lng2'))
                    if (lat_old == lat_new) and (lng_old == lng_new):
                        page += 1
                        list_data += data
                        if page <= 10:
                            continue
                        else:
                            break
                    else:
                        for item_rect in rects:
                            list_data += search_one_cate(index, item_rect, category, key)
                        break
                elif total > 20 * page:
                    page += 1
                    list_data += data
                    continue
                else:
                    list_data += data
                    break
            else:
                logger.error('在检索第 {} 个矩形区域的 {} 类信息出错：{}/{}'.format(index, category.get('category'),
                                                                               status, data))
                break
        return list_data
    except Exception as e:
        logger.error('在检索第 {} 个矩形区域的 {} 类信息出错：{}'.format(index, category.get('category'), e))
        return []


def search_one_rect(index, rect, categories, key):
    global stop
    begin = time.time()
    list_data = []
    for category in categories:
        if stop:
            break
        list_data += search_one_cate(index, rect, category, key)
    end = time.time()
    logger.debug('完成了第 {} 个矩形的所有类别获取，耗时：{:.2f}秒，供获取{}条数据'.format(index, (end-begin), len(list_data)))
    return list_data


def search_one_file(filename, index, categories, key):
    global stop
    begin = time.time()
    list_data = []
    rects = get_rect(filename)
    for i, rect in enumerate(rects):
        if stop:
            break
        list_data += search_one_rect('file:{}/rect:{}'.format(index, i), rect, categories, key)
    end = time.time()
    with open('poidata/rect_{}.poi'.format(index), 'w', encoding='utf-8') as f:
        for item in list_data:
            f.write('{}\n'.format(json.dumps(item)))
    logger.info('结束第 {} 个文件的检索并写入， 共有 {} 条数据， 共耗时：{:.2f} 秒'.format(index, len(list_data), (end-begin)))


def search_more_file(begin, end):
    rect_file = 'datafile/rect_{}.obj'
    category_file = 'datafile/poi_list_2'
    key_file = 'datafile/keys'
    global stop

    categories = get_category(category_file)
    keys = get_keys(key_file)
    for i in range(begin, end):
        if stop:
            break
        filename = rect_file.format(i)
        search_one_file(filename, i, categories, keys)
    logger.info('全部完成！')
