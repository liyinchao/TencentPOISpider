# _*_ coding:UTF-8 _*_
# 开发时间: 2019/10/24 8:50
# 文件名称: Config.py
# 开发人员: liaop
# 开发团队: sunyea
# 代码概述: 配置文件处理

import configparser


class ConfigDict(dict):
    def __getattr__(self, item):
        if item in self.keys():
            return self[item]
        else:
            return None

    def __setattr__(self, key, value):
        self[key] = value


def getConfig(file_name=None):
    try:
        parser = configparser.ConfigParser()
        if not file_name:
            file_name = 'conf/default.cfg'
        parser.read(file_name)
        config = ConfigDict()
        for section in parser.sections():
            config[section] = ConfigDict()
            for key in parser[section]:
                config[section][key] = parser.get(section, key)
    except:
        config = ConfigDict()
    return config
