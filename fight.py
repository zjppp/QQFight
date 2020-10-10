#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   fight.py
@Contact :   958615161@qq.com

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2020/8/8 20:53   zjppp      1.0         None
'''
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import configparser
import time

from Logger import Logger
from functions import login, kezhanlingjiang, wulinmengzhu, wending, mengxiangzhilv, huajuanmizong, huanjing, doushenta, \
    fenxiang, lilian, xialv, wulin, xieshenmibao, gongfeng, shiergong, xuyuan, huangjinliansai, yuanzhengjun, \
    liumenhuiwu, dianfeng, huiliu, menpai, tiaozhanboss, tiguan, biaoxingtianxia, liangcao, shengri, meirijiangli, \
    doudouyueka, yaoqing, liwu, shanghui, qunxiongzhulu, kuangdong, bangpairenwu, bangpaijitan, jingjichang, sendmsg
from multiprocessing import Process

def runfight(user):
    conf = configparser.ConfigParser()
    conf.read("./conf/user.conf")  # 文件路径读conf
    userConf = dict(conf.items(user)) # 用户配置字典
    # print(userConf)

    # 配置logger
    log = Logger(logname=time.strftime("%Y-%m-%d", time.localtime()), loglevel=1,
                     logger=userConf.get("username")).getlog()

    login(userConf,conf,user,log,0)
    kezhanlingjiang(log)  # 客栈领奖
    wulinmengzhu(1,log)  # 武林盟主
    wending(3, 0, log)  # 问鼎天下 暂时可用 #todo 1.助威 2.优先打标记
    mengxiangzhilv(log)  # 梦想之旅 to do 区域领奖
    huajuanmizong(log)  # 画卷迷踪
    huanjing(log)  # 幻境
    doushenta(log)  # 斗神塔 todo 优化线程执行逻辑
    fenxiang(log)  # 分享 todo 领奖
    lilian(6394, 3, log)  # 历练 todo 优化，bossid放在一个list里
    lilian(6393, 3, log)
    xialv(log)  # 侠侣
    wulin(log,1)  # 武林大会 todo 手机区报名优化
    xieshenmibao(log)  # 邪神秘宝
    gongfeng(log, 3089)  # 帮派供奉
    shiergong(log, 1011)  # 十二宫
    xuyuan(userConf.get("username"),log)  # 许愿 fixme 领奖
    huangjinliansai(log)  # 帮派黄金联赛 todo
    yuanzhengjun(log)  # 帮派远征军
    liumenhuiwu(log)  # 六门会武
    dianfeng(log)  # 巅峰之战
    huiliu(log)  # 回流
    menpai(userConf.get("username"),log)  # 门派（包括邀请赛）
    tiaozhanboss(log, userConf.get("username"))
    tiguan(log)  # 踢馆 todo 再看看
    liangcao(log) #todo 领奖
    biaoxingtianxia(userConf.get("username"),log)  # 镖行天下
    shengri(log)  # 生日 todo 50次领奖
    meirijiangli(log)  # 每日奖励（4礼包）
    doudouyueka(userConf.get("username"),log)  # 斗豆月卡
    yaoqing(log)  # 邀请（转盘抽2次奖）
    liwu(log)  # 礼物
    shanghui(log)  # 商会 todo
    qunxiongzhulu(log)  # 群雄 todo 报名优化（应该没问题了）
    kuangdong(log)  # 矿洞 todo 待优化 + 领奖
    bangpairenwu(userConf.get("username"),log) #帮派任务
    bangpaijitan(log) # 祭坛 todo
    jingjichang(log)
    # sendmsg()

if __name__ == "__main__":
    conf = configparser.ConfigParser()
    conf.read("./conf/user.conf")  # 文件路径
    userlist = conf.get("userlist", "list").replace("[", "").replace("]", "")
    ulist = userlist.split(",")
    for u in ulist:
        try:
            QQFight = Process(target=runfight,args=(u,))
            QQFight.start()
        except:
            print("Error: 无法启动线程")


