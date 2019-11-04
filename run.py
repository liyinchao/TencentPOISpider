# _*_ coding:UTF-8 _*_
# 开发时间: 2019/10/24 10:11
# 文件名称: run.py
# 开发人员: liaop
# 开发团队: sunyea
# 代码概述: 执行指令

import time
import json
import pymysql as mysql
from utility.Config import getConfig
from utility.Global import Global
from utility.Logger import getLogger

Global.config = getConfig('conf/default.cfg')


def write_poi_kind(logger):
    '''
    生成poi类别文件
    :param logger:
    :return:
    '''
    from TencentPOI import TencentPOI
    if TencentPOI.parse_business('datafile/poi_list', 'li', 2):
        logger.debug('获取成功')
    else:
        logger.debug('获取失败')


def write_rectangle(logger):
    '''
    生成网格文件
    :param logger:
    :return:
    '''
    from TencentPOI import TencentPOI
    if TencentPOI.split_rectangle('datafile/rect',
                                  Global.config.chengdu.blat,
                                  Global.config.chengdu.blng,
                                  Global.config.chengdu.elat,
                                  Global.config.chengdu.elng,
                                  Global.config.chengdu.step):
        logger.debug('生成成功')
    else:
        logger.debug('生成失败')


def write_rectangle2(logger):
    '''
    将网格进行分割，并写入网格批次文件， split为每个文件保存多少个网格
    :param logger:
    :return:
    '''
    from TencentPOI import TencentPOI
    if TencentPOI.split_rectangle('datafile/rect2',
                                  Global.config.chengdu2.blat,
                                  Global.config.chengdu2.blng,
                                  Global.config.chengdu2.elat,
                                  Global.config.chengdu2.elng,
                                  Global.config.chengdu2.step,
                                  split=40):
        logger.debug('生成成功')
    else:
        logger.debug('生成失败')


def search_rectangles(from_index, to_index, logger):
    '''
    检索网格批次，以生成的网格文件为单位，1个文件为一个批次
    :param from_index: 开始的批次
    :param to_index: 结束的批次（不包含）
    :param logger:
    :return:
    '''
    from TencentPOI import TencentPOI
    categories = []
    with open('datafile/poi_list_2', 'r', encoding='utf-8') as f:
        for line in f.readlines():
            categories.append(line.replace('\n', ''))
    for index in range(from_index, to_index):
        rects = []
        filename = 'datafile/rect_{}.obj'.format(index)
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                rects.append(json.loads(line))
        keys = Global.config.tencent.key.split(',')
        if TencentPOI.search_rects('poidata/rect_{}.poi'.format(index), index, rects, categories, keys):
            logger.debug('检索成功')
        else:
            logger.debug('检索失败')


def save_db(filename, logger):
    '''
    将检索数据存入数据库
    :param filename: 检索数据文件名
    :param logger:
    :return:
    '''
    def s2db(value):
        if isinstance(value, str):
            return value.replace("'", '"').replace("\\", "")
        else:
            return value

    start = time.time()
    db = mysql.connect(Global.config.mysql.host, Global.config.mysql.uid,
                       Global.config.mysql.pwd, Global.config.mysql.dbname)
    cursor = db.cursor()
    sql = "insert into tencentpoi(id,title,address,tel,category1,category2,category3,type,lat,lng,adcode,province," \
          "city,district) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            try:
                obj = json.loads(line)
                category = obj.get('category')
                arr_cate = category.split(':')
                arr_cate += [None, None]
                cursor.execute(sql, args=(obj.get('id'), obj.get('title'), obj.get('address'), obj.get('tel'),
                                          arr_cate[0], arr_cate[1], arr_cate[2], obj.get('type'),
                                          obj.get('location').get('lat'), obj.get('location').get('lng'),
                                          obj.get('ad_info').get('adcode'), obj.get('ad_info').get('province'),
                                          obj.get('ad_info').get('city'), obj.get('ad_info').get('district')))
                db.commit()
            except Exception as e:
                # logger.error('入库异常：{}'.format(e))
                db.rollback()
    db.close()
    end = time.time()
    logger.info('本次执行用时：{:.2f}s'.format((end - start)))


if __name__ == '__main__':
    logger = getLogger('Main Run')
    start = time.time()
    for i in range(1, 40):
        filename = 'poidata/rect_{}.poi'.format(i)
        logger.debug('开始导入文件{}的数据'.format(filename))
        save_db(filename, logger)
    end = time.time()
    logger.info('全部执行用时：{:.2f}s'.format((end-start)))

    # import searchPOIDetail
    # searchPOIDetail.search_more_file(0, 1)
