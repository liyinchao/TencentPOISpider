# _*_ coding:UTF-8 _*_
# 开发时间: 2019/10/24 9:16
# 文件名称: TencentPOI.py
# 开发人员: liaop
# 开发团队: sunyea
# 代码概述: 基于腾讯地图的POI应用
from bs4 import BeautifulSoup
import requests
import json
from urllib import parse
import time
import os
from utility.Logger import getLogger


class BusinessItem(object):
    def __init__(self, title, id):
        self.title = title
        self.id = id
        self.childrens = []

    def add_children(self, children):
        nohave = True
        for item in self.childrens:
            if item.title == children.title:
                nohave = False
                break
        if nohave:
            self.childrens.append(children)

    def to_dict(self):
        rt = {'title': self.title, 'id': self.id}
        for child in self.childrens:
            if isinstance(rt.get('children', None), list):
                rt['children'].append(child.to_dict())
            else:
                rt['children'] = list()
                rt['children'].append(child.to_dict())
        return rt


class TencentPOI(object):
    logger = getLogger('TencentPOI')
    business_url = 'https://lbs.qq.com/webservice_v1/guide-appendix.html'
    search_url = 'https://apis.map.qq.com/ws/place/v1/search?boundary=rectangle({rect})&' \
                 'keyword={keywd}{category}&page_size=20&page_index={page}&' \
                 'key={key}'

    @classmethod
    def make_dir(cls, path):
        '''
        检查并创建文件夹
        :param path: 文件路径
        :return:
        '''
        path = os.path.dirname(path)
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if not os.path.exists(path):
            os.makedirs(path)

    @classmethod
    def _get_rectangles(cls, blat, blng, elat, elng, step):
        '''
        生成网格
        :param blat: 左下纬度
        :param blng: 左下经度
        :param elat: 右上纬度
        :param elng: 右上经度
        :param step: 步长
        :return: 网格矩形列表
        '''
        blat = float(blat)
        blng = float(blng)
        elat = float(elat)
        elng = float(elng)
        step = float(step)

        xlen = int((elng - blng) / step)
        ylen = int((elat - blat) / step)
        rectangles = []
        for i in range(xlen):
            for j in range(ylen):
                rectangle = {'lat1': blat + step * j,
                             'lng1': blng + step * i,
                             'lat2': blat + step * (j + 1),
                             'lng2': blng + step * (i + 1)}
                rectangles.append(rectangle)
        return rectangles

    @classmethod
    def parse_business(cls, filename, stype='tree', level=2):
        '''
        从腾讯地图服务获取Poi分类，并存入文件
        :param filename: 保存文件名
        :param stype: 保存类型 tree:树形对象；li: 队列
        :param level: 分类级别
        :return: boolean
        '''
        try:
            html = requests.get(cls.business_url)
            bs = BeautifulSoup(html.content.decode(), 'html.parser')
            items = {}
            lis = []
            index = 0
            for item in bs.find_all('tr'):
                one = item.find_all('td')[3].get_text()
                arr_one = one.split(':')
                arr_one += [None, None]
                name1 = arr_one[0]
                name2 = arr_one[1]
                name3 = arr_one[2]

                if stype == 'tree':
                    if name1 not in items.keys():
                        obj1 = BusinessItem(name1, index)
                        index += 1
                        items[name1] = obj1
                    if level > 1:
                        if name2:
                            obj2 = BusinessItem(name2, index)
                            index += 1
                            items[name1].add_children(obj2)
                    if level > 2:
                        if name3:
                            for child in items[name1].childrens:
                                if child.title == name2:
                                    obj3 = BusinessItem(name3, index)
                                    index += 1
                                    child.add_children(obj3)
                                    break
                else:
                    li = name1
                    if level > 1 and name2:
                        li += ':'+name2
                    if level > 2 and name3:
                        li += ':'+name3
                    if li not in lis:
                        lis.append(li)
            filename = '{}_{}'.format(filename, level)
            cls.make_dir(filename)
            with open(filename, 'w', encoding='utf-8') as f:
                if stype == 'tree':
                    for item in items.values():
                        f.write('{}\n'.format(item.to_dict()))
                else:
                    for li in lis:
                        f.write('{}\n'.format(li))
            cls.logger.info('类别已成功写入文件：{}'.format(filename))
            return True
        except Exception as e:
            cls.logger.error('获取poi类别出错：{}'.format(e))
            return False

    @classmethod
    def split_rectangle(cls, filename, blat, blng, elat, elng, step=0.01, split=50):
        '''
        通过设置的经纬度生成网格文件
        :param filename: 文件名
        :param blat: 左下纬度
        :param blng: 左下经度
        :param elat: 右上纬度
        :param elng: 右上经度
        :param step: 步长
        :param split: 多少个网格切分为一个文件
        :return: boolean
        '''
        try:
            rectangles = cls._get_rectangles(blat, blng, elat, elng, step)
            total = len(rectangles)
            index = 0
            num = 0
            f = None
            cls.make_dir(filename)
            for i, rect in enumerate(rectangles):
                if i % split == 0:
                    if f:
                        f.close()
                    num = 0
                if num == 0:
                    f = open('{}_{}.obj'.format(filename, index), 'w', encoding='utf-8')
                    index += 1
                f.write('{}\n'.format(json.dumps(rect)))
                num += 1
            if f:
                f.close()
            cls.logger.info('成功生成{}个网格文件，合计{}个网格'.format(index, total))
            return True
        except Exception as e:
            cls.logger.error('生成网格出错：{}'.format(e))
            return False

    @classmethod
    def _search_one(cls, index, rect, category, key):
        '''
        检索一次Poi数据
        :param index: 检索的索引
        :param rect: 区域范围
        :param category: 类型
        :param key:
        :return: poi列表
        '''
        try:
            parm = {}
            parm['rect'] = '{},{},{},{}'.format(rect.get('lat1'), rect.get('lng1'), rect.get('lat2'), rect.get('lng2'))
            arr_cate = category.split(':')
            parm['keywd'] = parse.quote(arr_cate[0])
            if len(arr_cate) > 1:
                parm['category'] = '&filter=category={}'.format(parse.quote(arr_cate[1]))
            else:
                parm['category'] = ''
            page = 1
            parm['page'] = page
            parm['key'] = key
            url = cls.search_url.format(**parm)
            response = requests.get(url)
            js = json.loads(response.content.decode())
            if int(js.get('status')) == 0:
                total = int(js.get('count'))
                if total > 200:
                    total = 200
                list_data = js.get('data', [])
                time.sleep(0.1)
                while total > 20 * page:
                    page += 1
                    parm['page'] = page
                    url = cls.search_url.format(**parm)
                    response = requests.get(url)
                    js = json.loads(response.content.decode())
                    list_data += js.get('data', [])
                    time.sleep(0.1)
                # cls.logger.debug('从{}检索 {} 的结果是 {} 条数据'.format(index, category, total))
                return list_data
            else:
                cls.logger.error('从{}检索 {} 失败，原因：{}/{}'.format(index, category,
                                                                 js.get('status'),
                                                                 js.get('message')))
                return None
        except Exception as e:
            cls.logger.error('{}检索出错：{}'.format(index, e))
            return None

    @classmethod
    def search_rects(cls, filename, index, rects, categories, keys):
        '''
        检索Poi
        :param filename: 保存文件名
        :param index: 网格索引
        :param rects: 多个网格
        :param categories: 多个类别
        :param keys: 多个key
        :return: boolean
        '''
        try:
            i = 0
            result = []
            begin = time.time()
            all_num = 0
            for num, rect in enumerate(rects):
                sindex = '第 {}/{} 块'.format(num, index)
                for category in categories:
                    all_num += 1
                    key = keys[i]
                    datas = cls._search_one(sindex, rect, category, key)
                    if datas is None:
                        i += 1
                        if i > 4:
                            i = 0
                        key = keys[i]
                        # time.sleep(0.5)
                        datas = cls._search_one(sindex, rect, category, key)
                    if datas:
                        result += datas
                    if all_num % 100 == 0:
                        cls.logger.debug('检索到：{}, 一共检索了 {} 次'.format(sindex, all_num))
            cls.make_dir(filename)
            with open(filename, 'w', encoding='utf-8') as f:
                for data in result:
                    cate = data.get('category')
                    arr_cate = cate.split(':')
                    arr_cate.append(None)
                    arr_cate.append(None)
                    value = {'id': data.get('id'), 'title': data.get('title'), 'address': data.get('address'),
                             'tel': data.get('tel'), 'cate1': arr_cate[0], 'cate2': arr_cate[1], 'cate3': arr_cate[2],
                             'type': data.get('type'), 'lat': data.get('location').get('lat'),
                             'lng': data.get('location').get('lng'), 'adcode': data.get('ad_info').get('adcode'),
                             'province': data.get('ad_info').get('province'), 'city': data.get('ad_info').get('city'),
                             'district': data.get('ad_info').get('district')}
                    f.write('{}\n'.format(json.dumps(value)))
            end = time.time()
            cls.logger.info('批量检索第 {} 批次的网格，合计 {} 条数据，共耗时 {:2f}s'.format(index, len(result),
                                                                         (end - begin)))
            return True
        except Exception as e:
            cls.logger.error('批量检索出错：{}'.format(e))
            return False




