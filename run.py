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
from utility.Logger import getLogger
from utility.Global import Global

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
    from TencentPOI import TencentPOI
    categories = []
    with open('datafile/poi_list_2', 'r', encoding='utf-8') as f:
        for line in f.readlines():
            categories.append(line.replace('\n', ''))
    for index in range(from_index, to_index):
        rects = []
        filename = 'datafile/rect2_{}.obj'.format(index)
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                rects.append(json.loads(line))
        keys = Global.config.tencent.key.split(',')
        if TencentPOI.search_rects('poidata/rect_{}.poi'.format(index), index, rects, categories, keys):
            logger.debug('检索成功')
        else:
            logger.debug('检索失败')


def save_db(filename, logger):
    def s2db(value):
        if isinstance(value, str):
            return value.replace("'", '"').replace("\\", "")
        else:
            return value

    db = mysql.connect(Global.config.mysql.host, Global.config.mysql.uid,
                       Global.config.mysql.pwd, Global.config.mysql.dbname)
    cursor = db.cursor()
    sql_base = "insert into tencentpoi values(null, '{id}', '{title}','{address}', '{tel}', '{cate1}', " \
               "'{cate2}', '{cate3}', {type}, {lat}, {lng}, {adcode}, '{province}', '{city}', '{district}');"
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            obj = json.loads(line)
            for k, v in obj.items():
                obj[k] = s2db(v)
            sql = sql_base.format(**obj)
            try:
                cursor.execute(sql)
                db.commit()
            except Exception as e:
                logger.debug(sql)
                logger.error('入库异常：{}'.format(e))
                db.rollback()
    db.close()
    logger.info('完成入库操作')


if __name__ == '__main__':
    logger = getLogger('Main Run')
    logger.debug('开始获取poi类别')
    start = time.time()
    search_rectangles(0, 1, logger)
    # write_rectangle2(logger)
    # save_db('poidata/rect_0.poi', logger)
    end = time.time()
    logger.info('本次执行用时：{:.2f}s'.format((end-start)))
