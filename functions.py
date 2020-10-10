#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   functions.py
@Contact :   958615161@qq.com

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2020/8/8 20:55   zjppp      1.0         None
"""
import json
import random
import re
import sys
import threading
import time
from datetime import datetime
from time import sleep

import requests
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities

from slideVerfication import SlideVerificationCode

today = time.strftime("%Y-%m-%d", time.localtime())

dayOfWeek = datetime.now().isoweekday()
hour = datetime.now().hour
minute = datetime.now().minute

header = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9',
    'referer': 'https://fight.pet.qq.com/',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest'
}
cookie = {}
req = requests.Session()
req.headers = header


def login(userconf, conf, user, log, longintype=0):
    """
    登录
    :param userconf:当前用户的配置
    :param conf:当前用户名
    :param user:
    :param log:
    :param longintype:
    :return:
    """
    log.info("---------------------------------------------------------")
    flag = False
    cookie = userconf.get("cookie")
    username = userconf.get("username")
    pwd = userconf.get("password")

    if len(str(cookie)) != 0:
        cookie = eval(cookie)
        flag = isLogin(header, cookie, username)  # 未过期-True
    if flag:
        print("cookie登录成功")

    else:
        try:
            print("cookie不存在或已失效，使用密码登录")
            # PhantomJS伪装chrome
            dcap = dict(DesiredCapabilities.PHANTOMJS)
            dcap['phantomjs.page.settings.userAgent'] = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36')
            driver = webdriver.PhantomJS(executable_path=r"phantomjs",desired_capabilities=dcap,service_args=['--ignore-ssl-errors=true'])
            # driver = webdriver.Chrome(executable_path='chromedriver')
            driver.implicitly_wait(3)
            if str(longintype).startswith("0"):
                # 方案0 移动端游戏入口登录
                log.info("准备登陆中.....")
                driver.get(
                    "http://ui.ptlogin2.qq.com/cgi-bin/login?appid=614038002&style=9&s_url=http%3A%2F%2Fdld.qzapp.z.qq.com%2Fqpet%2Fcgi-bin%2Fphonepk%3Fcmd%3Dindex%26channel%3D0")
                driver.find_element_by_id('u').clear()
                driver.find_element_by_id('u').send_keys(username)
                driver.find_element_by_id('p').clear()
                driver.find_element_by_id('p').send_keys(pwd)
                driver.find_element_by_id('go').click()
                sleep(5)
            else:
                # 方案1 空间游戏应用中心登录
                log.info("准备登陆中.....")
                driver.get(
                    "https://xui.ptlogin2.qq.com/cgi-bin/xlogin?appid=549000912&daid=5&s_url=https%3A%2F%2Fgame.qzone.qq.com%2F%3Ffrom%3Dgameapp&style=20&border_radius=1&target=top&maskOpacity=40&")
                driver.find_element_by_id('switcher_plogin').click()
                driver.find_element_by_id('u').clear()
                driver.find_element_by_id('u').send_keys(username)
                driver.find_element_by_id('p').clear()
                driver.find_element_by_id('p').send_keys(pwd)
                driver.find_element_by_id('login_button').click()
                sleep(5)

            currentUrl = str(driver.current_url)

            # 进行滑动验证
            if currentUrl.startswith("https://ui.ptlogin2.qq.com/cgi-bin/login"):
                log.info("本次登录出现滑动验证码，尝试自动识别中......")
                sleep(5)
                # 进行滑动验证
                # 1定位验证码所在的iframe,并进行切换
                v_frame = driver.find_element_by_id('tcaptcha_iframe')
                driver.switch_to.frame(v_frame)
                # 2获取验证码滑块图元素
                sli_ele = driver.find_element_by_id('slideBlock')
                # 3获取验证码背景图的元素
                bg_ele = driver.find_element_by_id('slideBg')
                # 4 识别滑块需要滑动的距离
                # 4.1识别背景缺口位置
                sv = SlideVerificationCode()
                distance = sv.get_element_slide_distance(sli_ele, bg_ele)
                # 4.2 根据页面的缩放比列调整滑动距离
                dis = distance * (280 / 680) + 10
                # 5 获取滑块按钮
                sli_btn = driver.find_element_by_id('tcaptcha_drag_thumb')
                # 6拖动滑块进行验证
                flag = sv.slide_verification(driver, sli_btn, dis)
                sleep(3)

            currentUrl = str(driver.current_url)
            flag = ""
            if str(longintype).startswith("0"):
                flag = "https://dld.qzapp.z.qq.com/qpet/cgi-bin"
            else:
                flag = "https://game.qzone.qq.com/?from=gameapp"
            if currentUrl.startswith(flag):
                log.info("登录成功，准备开始执行任务")
            else:
                log.info("登陆失败，自动退出")
                sleep(1)
                driver.quit()
                sleep(1)
                sys.exit()
            sleep(5)
            cookie = getCookie(driver, log)
            # print("写入：" + str(user)) #debug
            # print(cookie)
            conf.read("./conf/user.conf")  # 文件路径读conf
            conf.set(user, "cookie", str(cookie))  # 修改指定section 的option
            with open('./conf/user.conf', 'w') as configfile:
                conf.write(configfile)
        finally:
            driver.quit()
    req.cookies.update(cookie)


def isLogin(header, cookie, qqnum):
    response = req.get("https://fight.pet.qq.com/cgi-bin/petpk?cmd=view&kind=0&sub=2&type=4&selfuin=" + str(qqnum),
                       headers=header, cookies=cookie)
    json = parser(response)
    flag = False
    if str(json.get("msg")).startswith("OK"):
        flag = True
    return flag


def getCookie(driver, log):
    """
    获取cookie
    :param driver:webdriver
    :return: cookie_dict cookie字典
    """
    cookie_list = driver.get_cookies()
    cookie_dict = {}
    for cookie in cookie_list:
        if 'name' in cookie and 'value' in cookie:
            cookie_dict[cookie['name']] = cookie['value']
    log.info("获取cookie成功")
    return cookie_dict


# 当前个人状态todo
def getPersonalStatus(html):
    """
    :param html:
    :return:
    """
    str1 = str(html)
    regex = []
    regex.append(r"等级:[1-9]\d*（[1-9]\d*/[1-9]\d*）")  # 匹配等级
    regex.append(r"体力:[1-9]\d*/[1-9]\d*")  # 匹配体力
    regex.append(r"活力:[1-9]\d*/[1-9]\d*")  # 匹配活力
    regex.append(r"生命:[1-9]\d*\+[1-9]\d*")  # 匹配生命
    regex.append(r"力量:[1-9]\d*\+[1-9]\d*")  # 匹配力量
    regex.append(r"敏捷:[1-9]\d*\+[1-9]\d*")  # 匹配敏捷
    regex.append(r"速度:[1-9]\d*\+[1-9]\d*")  # 匹配速度
    statusDict = {}
    for i in range(7):
        value = re.compile(regex[i]).search(str1).group()
        var = value.split(":", 2)
        statusDict[var[0]] = var[1]
    return statusDict


def generateID(idtype):
    '''
    生成问鼎id，生成规则：
    1级:(1-4)110（1-4）0000  ->  a110b0000
    2级:(1-4）210（0-9）00（01-10）  ->  a210c00d
    3级:(1-4）310（0-9）（0001-4000）  ->  a310ce
    :param idtype:生成id的类型
    :return: id
    '''
    a = random.randint(1, 4)
    b = random.randint(1, 4)
    c = random.randint(0, 9)
    d = random.randint(1, 10)
    d = str(d).zfill(2)
    e = random.randint(1, 4000)
    e = str(e).zfill(4)

    if idtype == 3:
        return str(a) + "310" + str(c) + e
    elif idtype == 2:
        return str(a) + "210" + str(c) + "00" + d
    else:
        return str(a) + "110" + str(b) + "0000"


def kezhanlingjiang(log):
    """
    客栈领奖
    :param log: 日志输出
    :return:
    """
    kezhandajianlingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=knight&op=14&type=1&id=%(id)s"
    kezhanzhudianlingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=knight&op=14&type=2&id=%(id)s"
    for i in range(3):
        if 8 <= hour < 20:
            j = requestURL(kezhanzhudianlingjiang % {"id": str(i + 1)})
            if str(j.get("msg")).startswith("奖励已经领取过了"):
                continue
            log.info(j.get("msg"))
        else:
            j = requestURL(kezhandajianlingjiang % {"id": str(i + 1)})
            if str(j.get("msg")).startswith("奖励已经领取过了"):
                continue
            log.info(j.get("msg"))


def mengxiangzhilv(log):
    """
    梦想之旅 todo 领奖
    :param log: 日志输出
    :return:
    """
    mengxiangzhilvchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=dreamtrip&bmapid=0&sub=0"
    mengxiangzhilvputong = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=dreamtrip&smapid=0&sub=1"
    mengxiangzhilvquyujiangli = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=dreamtrip&bmapid=%(bmapid)s&sub=2"

    j = requestURL(mengxiangzhilvchaxun)
    curid = j.get("curid")  # 当前岛屿id
    normalticket = j.get("normalticket")
    if int(normalticket) > 0:
        # 普通旅行1次
        j = requestURL(mengxiangzhilvputong)
        msg = j.get("msg")
        if not str(msg).startswith("当前没有普通机票"):
            log.info("梦想之旅-普通旅行：" + msg)
    # 区域领奖
    j = requestURL(mengxiangzhilvchaxun)
    smap_info = j.get("smap_info")  # 当前岛屿信息
    bmap_info = j.get("bmap_info")  # 所有岛屿信息
    flag = True
    for item in smap_info:
        if int(item.get("status")) != 1:
            flag = False
            break
    if flag == True:
        j = requestURL(mengxiangzhilvquyujiangli % {"bmapid": curid})
        msg = j.get("msg")
        log.info("梦想之旅-区域领奖：" + msg)
    sum = 0
    for item in bmap_info:
        sum = sum + int(item.get("status"))
    if sum == 4:  # 4个区域全为1
        pass  # todo 领全区奖励

    pass


def huajuanmizong(log):
    """
    画卷迷踪
    :param log:
    :return:
    """
    huajuanmizongchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=scroll_dungeon"
    huajuanmizong = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=scroll_dungeon&op=fight&buff=0"

    j = requestURL(huajuanmizongchaxun)
    free_times = j.get("free_times")
    pay_times = j.get("pay_times")
    if int(free_times) + int(pay_times) == 0:
        return
    # 打5次
    for i in range(10):
        j = requestURL(huajuanmizong)
        msg = j.get("msg")
        if str(msg).startswith("没有挑战次数"):
            break
        else:
            log.info("画卷迷踪-挑战：" + msg)


def qunxiongzhulu(log):
    """
    群雄逐鹿
    :param log:
    :return:
    """
    qunxiongbaoming = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=thronesbattle&op=signup"
    qunxionglingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=thronesbattle&op=drawreward"
    qunxiongchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=thronesbattle"
    qunxiongpaihangbangchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=thronesbattle&op=queryrank&type=season&zone=%(zone)s"
    qunxiongpaihangbanglingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=thronesbattle&op=drawrankreward"

    # 1.报名
    if (dayOfWeek == 5 and hour >= 14) or (dayOfWeek == 1 and hour < 14) or (6 <= dayOfWeek <= 7):
        j = requestURL(qunxiongbaoming)
        msg = j.get("msg")
        log.info("群雄逐鹿-报名：" + msg)
    # 2.领奖
    j = requestURL(qunxionglingjiang)
    msg = j.get("msg")
    if str(msg).startswith("你已经领取"):
        pass
    else:
        log.info("群雄逐鹿-领奖" + msg)
    # 3.排行榜领奖
    # response = requests.get(URL.qunxiongpaihangbang, headers=header, cookies=cookie)
    # HTML = response.content.decode('utf-8')
    j = requestURL(qunxiongchaxun)
    signed_up_zone = j.get("signed_up_zone")
    if str(signed_up_zone) in ["1", "2", "3", "4"]:
        j = requestURL(qunxiongpaihangbangchaxun % {"zone": str(signed_up_zone)})
        self_rank = j.get("self_rank")
        if int(self_rank) > 0 and int(self_rank) <= 1000:
            j = requestURL(qunxiongpaihangbanglingjiang)
            msg = j.get("msg")
            if str(msg).startswith("本届已经领取排行榜奖励"):
                pass
            else:
                log.info("群雄逐鹿-排行榜领奖" + msg)


def huanjing(log):
    """
    幻境
    :param log:
    :return:
    """
    huanjingtuichu = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=misty&op=return"
    huanjingjinru = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=misty&op=start&stage_id=%(stage_id)s"
    huanjingzhandou = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=misty&op=fight"

    # 退出副本
    j = requestURL(huanjingtuichu)
    # 进入副本(id为1-20)
    j = requestURL(huanjingjinru % {"stage_id": "20"})
    msg = j.get("msg")
    if str(msg).startswith("副本未开通") or str(msg).startswith("您的挑战次数已用完，请明日再战"):
        log.info("幻境-进入副本：" + msg)
    else:
        cur_stage = j.get("cur_stage")
        log.info("幻境-进入副本：第" + str(cur_stage) + "关")
        # 战斗
        for i in range(5):
            j = requestURL(huanjingzhandou)
            msg = j.get("msg")
            log.info("幻境-挑战：" + msg)
    # 退出副本
    j = requestURL(huanjingtuichu)
    msg = j.get("msg")
    if str(msg).startswith("当前副本未结束"):
        pass
    else:
        challenge_times = j.get("challenge_times")
        log.info("幻境-退出副本：当前剩余挑战次数 " + challenge_times)


def lilian(bossid, times, log):
    """
    历练指定bossid，打times次
    :param bossid: boss的id
    :param times: 挑战次数（最大3次）
    :param log:
    :return:
    """
    lilian = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=mappush&type=1&npcid=%(npcid)s"

    for i in range(min(int(times), 3)):
        j = requestURL(lilian % {"npcid": str(bossid)})
        msg = j.get("msg")
        if str(msg) == "":
            log.info("历练：挑战成功")
        else:
            log.info("历练：" + msg)


def xuyuan(username, log):
    """
    许愿
    :param username:
    :param log:
    :return:
    """
    xuyuanjinrilingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=wish&sub=3"
    xuyuanjinri = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=wish&sub=2"
    xuyuanchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=wish&sub=1"
    xuyuansantian = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=wish&sub=6"

    # 领取昨日许愿奖励
    j = requestURL(xuyuanjinrilingjiang)
    if j != None:
        msg = j.get("msg")
        if not str(msg).startswith("很抱歉"):
            name = j.get("name")
            num = j.get("num")
            log.info("许愿：获取" + name + "*" + num)
    # 斗自己一次，确保有首胜
    fight(log, username)
    # 进入今日许愿
    j = requestURL(xuyuanjinri)
    msg = j.get("msg")
    if str(msg).startswith("许愿失败，请再试一次"):
        pass
    else:
        log.info("许愿：" + msg)
    j = requestURL(xuyuanchaxun)
    days = j.get("days")
    if str(days).startswith("3"):
        # 领取连续3天许愿奖励
        j = requestURL(xuyuansantian)
        msg = j.get("msg")
        log.info("许愿：" + msg)


def huangjinliansai(log):
    """
    黄金联赛 todo 赛季末领奖，战斗
    :param log:
    :return:
    """
    huangjinliansailingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factionleague&op=5"

    # 1.黄金联赛领奖
    j = requestURL(huangjinliansailingjiang)
    msg = j.get("msg")
    log.info("黄金联赛：" + msg)


def fight(log, qqnum):
    """
    挑战指定qq号
    :param log:
    :param qqnum: QQ号
    :return:
    """
    qqfight = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fight&puin=%(puin)s"

    response = req.get(qqfight % {"puin": str(qqnum)})
    # result = jiexifanhuixiaoxi(response,"result")


def shiergong(log, scene_id=1011):
    """
    十二宫
    :param log:
    :param scene_id: 场景id，范围为1000-1011
    :return:
    """
    shiergongchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=zodiacdungeon&op=query"
    shiergong = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=zodiacdungeon&op=autofight&pay_recovery_count=0&scene_id=%(scene_id)s"
    j = requestURL(shiergongchaxun)
    left_challenge_times = j.get("left_challenge_times")
    if int(left_challenge_times) != 0:
        j = requestURL(shiergong % {"scene_id": str(scene_id)})
        msg = j.get("msg")
        log.info("十二宫-挑战：" + msg)


def tiguan(log):
    """
    踢馆
    :param log:
    :return:
    """
    tiguanchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_challenge&subtype=0"
    tiguanzhuanpan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_challenge&subtype=6"
    tiguanshilian = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_challenge&subtype=2"
    tiguantiaozhan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_challenge&subtype=3"
    tiguanlingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_challenge&subtype=9"
    tiguanpaihangbanglingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_challenge&subtype=10"

    j = requestURL(tiguanchaxun)
    isFightTime = j.get("isFightTime")
    isAwardTime = j.get("isAwardTime")
    if str(isFightTime).startswith("1"):
        highRadio = j.get("highRadio")
        figntNpcTimes = j.get("figntNpcTimes")
        MaxFightNpcTimes = j.get("MaxFightNpcTimes")
        if str(highRadio).startswith("1"):
            j = requestURL(tiguanzhuanpan)
            msg = j.get("msg")
            if not str(msg).startswith("您已经使用过1次"):
                log.info("踢馆-转盘：" + msg)
        for i in range(int(MaxFightNpcTimes) - int(figntNpcTimes)):
            j = requestURL(tiguanshilian)
            msg = j.get("msg")
            log.info("踢馆-试炼：" + msg)
        for i in range(30):
            j = requestURL(tiguantiaozhan)
            msg = j.get("msg")
            if str(msg).startswith("（"):
                log.info("踢馆-挑战：" + msg)
            else:
                break
    if str(isAwardTime).startswith("1"):
        j = requestURL(tiguanlingjiang)
        msg = j.get("msg")
        if not str(msg).startswith("您已领取过奖励"):
            log.info("踢馆-领奖：" + msg)
        j = requestURL(tiguanpaihangbanglingjiang)
        msg = j.get("msg")
        if not str(msg).startswith("抱歉，您已经领取过奖励"):
            log.info("踢馆-领奖：" + msg)


def liangcao(log):
    """
    粮草
    :param log:
    :return:
    """
    liangcaochaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=forage_war"
    liangcaolingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=forage_war&subtype=6"
    liangcaojingongchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=forage_war&subtype=3"
    liangcaobaoxiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=forage_war&subtype=5"

    if (dayOfWeek == 2 and hour >= 6) or (dayOfWeek == 3 and hour < 6):
        j = requestURL(liangcaobaoxiang)
        msg = j.get("msg")
        if not str(msg).startswith("你已领取过该奖励"):
            log.info("粮草-领奖：" + msg)
    else:
        j = requestURL(liangcaochaxun)
        gift = j.get("gift")
        if str(gift).startswith("1"):
            j = requestURL(liangcaolingjiang)
            msg = j.get("msg")
            log.info("粮草-领奖：" + msg)


def kuangdong(log):
    """
    矿洞
    :param log:
    :return:
    """
    kuangdongchakan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factionmine"
    kuangdongzhandou = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factionmine&op=fight"
    kuangdonglingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factionmine&op=reward"

    j = requestURL(kuangdongchakan)
    reward_rank = j.get("reward_rank")
    fight_times = j.get("fight_times")
    current_dungeon_pos = j.get("current_dungeon_pos")
    if int(reward_rank) > 0:  # 矿洞领奖
        reward_message = j.get("reward_message")
        mines = j.get("mines")
        j = requestURL(kuangdonglingjiang)
        msg = j.get("msg")
        log.info("矿洞-领奖：" + reward_message + "获得矿石" + mines + "。" + msg)
    if 1 <= int(current_dungeon_pos) <= 15 and int(fight_times) < 3:
        for i in range(3 - int(fight_times)):
            j = requestURL(kuangdongzhandou)
            msg = j.get("msg")
            log.info("矿洞-挑战：" + msg)


def xieshenmibao(log):
    """
    邪神秘宝
    :param log:
    :return:
    """
    xieshenmibaochaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=tenlottery"
    xieshengaoji = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=tenlottery&type=0&op=2"
    xieshenjipin = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=tenlottery&type=1&op=2"

    j = requestURL(xieshenmibaochaxun)
    advanced = j.get("advanced")
    extreme = j.get("extreme")
    extreme = j.get("extreme")

    if str(advanced.get("ifFree")).startswith("1"):  # 0-没有免费次数，1-有免费次数
        j = requestURL(xieshengaoji)
        msg = j.get("msg")
        log.info("邪神秘宝-紫色秘宝：" + msg)
    if str(extreme.get("ifFree")).startswith("1"):  # 0-没有免费次数，1-有免费次数
        j = requestURL(xieshenjipin)
        msg = j.get("msg")
        log.info("邪神秘宝-橙色秘宝：" + msg)


def dianfeng(log):
    """
    巅峰之战
    :param log:
    :return:
    """
    dianfengchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=gvg&sub=0"
    dianfengsuijibaoming = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=gvg&sub=1&group=0"
    dianfenglingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=gvg&sub=4"

    j = requestURL(dianfengchaxun)
    userinfo = j.get("userinfo")
    if ((dayOfWeek == 1 and hour >= 6) or (dayOfWeek == 2 and hour < 24)) and str(userinfo["group"]).startswith("0"):
        # 巅峰随机报名 每周一早上6点~周二24点
        j = requestURL(dianfengsuijibaoming)
        msg = j.get("msg")
        log.info("巅峰之战-报名：" + msg)
    # 领奖
    j = requestURL(dianfenglingjiang)
    msg = j.get("msg")
    if str(msg).startswith("您已经领取过了"):
        pass
    else:
        log.info("巅峰之战-领奖：" + msg)
    if hour >= 6 and hour < 24 and dayOfWeek >= 3 and dayOfWeek <= 7:
        j = requestURL(dianfengchaxun)
        userinfo = j.get("userinfo")
        chall_status = userinfo.get("chall_status")
        if str(chall_status).startswith("2"):
            pass
        else:
            try:
                dianfeng = threading.Thread(target=dianfengrun, args=(log,))
                dianfeng.start()
            except:
                log.error("Error: 无法启动线程")


def gongfeng(log, id=3089):
    """
    供奉
    :param log:
    :param id: 要供奉物品的id  3089还魂丹
    :return:
    """

    gongfeng = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=feeddemo&id=%(id)s"
    wupinchaxun = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?zapp_uin=&sid=&channel=0&g_ut=1&cmd=owngoods&id=%(id)s"

    j = requestURL(gongfeng % {"id": str(id)})
    msg = j.get("msg")
    if str(msg).startswith("每天最多供奉5次"):
        log.info("供奉守护神：" + msg)
    else:
        # todo 手机端页面解析
        response = req.get(wupinchaxun % {"id": str(id)})
        html = response.content.decode("utf-8")
        pattern = re.compile('名称：[\u4e00-\u9fa5]+')
        name = pattern.search(str(html)).group()
        name = str(name).replace("名称：", "")
        log.info("供奉守护神：供奉1个" + str(name) + "。" + msg)


def fenxiang(log):
    """
    一键分享
    :param log:
    :return:
    """
    fenxiangsuoyou = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?zapp_uin=&sid=&channel=0&g_ut=1&cmd=sharegame&subtype=6"

    response = req.get(fenxiangsuoyou)  # 手机端操作，不做处理
    log.info("分享：一键分享完成")


def wulin(log, baomingtype=1):
    """
    武林报名
    :param log:
    :param baomingtype: 报名的类型  0-手机武林 1-电脑武林
    :return:
    """
    wulinchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=showwulin"
    diannaowulin = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=signup&id=%(id)s0306"
    shoujiwulin = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?zapp_uin=&sid=&channel=0&g_ut=1&cmd=fastSignWulin"

    # 1.获取当前届数
    j = requestURL(wulinchaxun)
    period = j.get("period")
    if str(baomingtype).startswith("1"):
        # 2.1报名电脑武林
        # print(str(period) + "0306")
        # j = requestURL(diannaowulin %{"id" : str(period) + "0306"})
        j = requestURL(diannaowulin % {"id": str(period)})
        msg = j.get("msg")
        log.info("武林大会电脑(第" + str(period) + "届)：" + msg)
    elif str(baomingtype) == "0":
        # 2.2报名手机武林
        response = req.get(shoujiwulin)
        j = requestURL(wulinchaxun)  # 直接查询报名的结果
        msg = j.get("msg")
        log.info("武林大会手机(第" + str(period) + "届)：" + msg)
    else:
        pass


def xialv(log):
    """
    侠侣报名
    :param log:
    :return:
    """
    xialv = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=couplefight&subtype=4"

    j = requestURL(xialv)
    msg = j.get("msg")
    log.info("侠侣争霸赛：" + msg)


def menpai(username, log):
    """
    门派
    :param username:
    :param log:
    :return:
    """
    menpailiutang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=%(op)s"
    menpaishangxiangputong = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sect&type=free&op=fumigate"
    menpaishangxianggaoxiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sect&type=paid&op=fumigate"
    menpaimuzhuang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sect&op=trainwithnpc"
    menpaitongmen = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sect&op=trainwithmember"
    menpaiduihuanzhanshu = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=exchange&type=1249&subtype=2&times=%(times)s"  # 战书兑换
    menpaiqiecuozhangmen = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sect&op=trainingwithcouncil&rank=1&pos=1"
    menpaiqiecuoshouzuo = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sect&op=trainingwithcouncil&rank=2&pos=%(pos)s"
    menpaiqiecuotangzhu = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sect&op=trainingwithcouncil&rank=3&pos=%(pos)s"
    menpairenwulingjinag = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sect_task&subtype=2&task_id=%(task_id)s"
    shuxingchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=viewattr&puin=%(puin)s"
    chakanhaoyou = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=view&kind=1&sub=1&selfuin=%(selfuin)s"
    ledou = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fight&puin=%(puin)s"  # 挑战好友
    menpaiputongxinfasuiji = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sect_art&subtype=2&art_id==%(art_id)s&times=1"
    menpaiyaoqingsaixinxi = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=secttournament"
    menpaiyaoqingsaibaoming = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=secttournament&op=signup"
    menpaiyaoqingsaizhandou = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=secttournament&op=fight"
    menpaiyaoqingsaipaihangbang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=secttournament&op=showlastseasonrank"
    menpaiyaoqingsailingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=secttournament&op=getrankandrankingreward"

    # 1.进入六堂
    for item in ["sect_art", "sect_trump", "sect&op=showcouncil", "sect_task", "sect&op=showtraining",
                 "sect&op=showincense"]:
        requestURL(menpailiutang % {"op": str(item)})
    # 2.上香
    j = requestURL(menpaishangxiangputong)
    msg = j.get("msg")
    if not str(msg).startswith("每日免费上香次数已达上限"):
        log.info("门派-上香：" + msg)
    # todo 优化逻辑，先判断数量，再上香
    j = requestURL(menpaishangxianggaoxiang)
    msg = j.get("msg")
    if str(msg).startswith("门派高香数量不足"):
        j = requestURL(menpaishangxianggaoxiang)
        msg = j.get("msg")
        log.info("门派-兑换：" + msg)
    if not str(msg).startswith("每日上高香次数已达上限"):
        log.info("门派-上香：" + msg)
    # 3.训练
    j = requestURL(menpailiutang % {"op": "sect&op=showtraining"})
    npc_challenged_times = j.get("npc_challenged_times")
    member_challenged_times = j.get("member_challenged_times")
    if not str(npc_challenged_times).startswith("1"):
        j = requestURL(menpaimuzhuang)  # 1次木桩
        msg = j.get("msg")
        log.info("门派-木桩训练：" + msg)
    if not str(member_challenged_times).startswith("2"):
        for i in range(2 - int(member_challenged_times)):
            j = requestURL(menpaitongmen)  # 2次同门
            msg = j.get("msg")
            if str(msg).startswith("门派战书数量不足"):
                i = i - 1
                j = requestURL(menpaiduihuanzhanshu % {"times": "1"})
                msg = j.get("msg")
                log.info("门派-兑换：" + msg)
            else:
                log.info("门派-同门切磋：" + msg)
    # 4.门派切磋
    j = requestURL(menpaiqiecuozhangmen)  # 打掌门
    msg = j.get("msg")
    log.info("门派-切磋：" + msg)
    for i in range(2):
        j = requestURL(menpaiqiecuoshouzuo % {"pos": str(i + 1)})  # 打首座1,2
        msg = j.get("msg")
        log.info("门派-切磋：" + msg)
    for i in range(4):
        j = requestURL(menpaiqiecuotangzhu % {"pos": str(i + 1)})  # 打堂主1,2,3,4
        msg = j.get("msg")
        log.info("门派-切磋：" + msg)
    # 5.门派任务
    j = requestURL(menpailiutang % {"op": "sect_task"})
    task = j.get("task")
    for i in range(3):
        id = task[i].get("id")
        state = task[i].get("state")
        if str(state) == "2":
            continue
        elif str(state) == "1":
            j = requestURL(menpairenwulingjinag % {"task_id": str(id)})
            msg = j.get("msg")
            log.info("门派-任务领奖：" + msg)
        elif str(state) == "0":
            if str(id) == "101":  # todo 打一次其他门派成员
                j = requestURL(menpailiutang % {"op": "sect"})
                selfsect = j.get("sect")  # 本人门派
                j = requestURL(shuxingchaxun % {"puin": str(username)})
                level = j.get("level")
                j = requestURL(chakanhaoyou % {"selfuin": str(username)})
                list = []
                info = j.get("info")
                for i in info:
                    # 筛选非本门派且等级差10以内的好友,且今日未挑战
                    if not str(i.get("sect")).startswith("0") and not str(i.get("sect")).startswith(
                            selfsect) and not str(i.get("enable")).startswith("0"):
                        if int(level) - 10 <= int(i.get("lilian")) <= int(level) + 10:
                            list.append(i)
                if len(list) == 0:
                    for i in info:
                        # 只筛选非本门派,且今日未挑战
                        if not str(i.get("sect")).startswith("0") and not str(i.get("sect")).startswith(
                                selfsect) and not str(i.get("enable")).startswith("0"):
                            list.append(i)
                # print((list))
                for i in list:
                    j = requestURL(ledou % {"puin": str(i.get("uin"))})
                    if j != None:
                        log.info("门派-任务：挑战好友 " + i.get("name") + "(" + i.get("uin") + ")")
                        break
            elif str(id) == "104":  # 修炼1次心法
                for i in range(10):  # 随机修炼心法，尝试10次不成功就退出
                    j = requestURL(menpaiputongxinfasuiji % {"art_id": str(random.randint(101, 118))})
                    msg = j.get("msg")
                    if str(msg).startswith("修炼成功"):
                        log.info("门派-普通心法：" + msg)
                        break
                j = requestURL(menpairenwulingjinag % {"task_id": str(id)})
                msg = j.get("msg")
                log.info("门派-任务领奖：" + msg)
            elif str(id) == "109" or str(id) == "110":  # 109查看一次同门资料，110查看一次其他门派成员的资料
                # 统一查看6个门派的信息 https://fight.pet.qq.com/cgi-bin/petpk?cmd=visit&puin=
                for uin in ["51215628", "1213197377", "526210932", "1532252524", "2648480160",
                            "294474047"]:  # 丐帮 华山 峨眉 少林 武当 明教
                    requestURL("https://fight.pet.qq.com/cgi-bin/petpk?cmd=visit&puin=" + str(uin))
                j = requestURL(menpairenwulingjinag % {"task_id": str(id)})
                msg = j.get("msg")
                log.info("门派-任务领奖：" + msg)
            else:
                pass
        else:
            pass
    # 6.门派邀请赛
    # 6.1领奖
    j = requestURL(menpaiyaoqingsaipaihangbang)
    has_reward = j.get("has_reward")
    if str(has_reward).startswith("1"):
        j = requestURL(menpaiyaoqingsailingjiang)
        msg = j.get("msg")
        log.info("门派邀请赛-领奖" + msg)
    # 6.2查看自己的报名信息
    j = requestURL(menpaiyaoqingsaixinxi)
    in_group = j.get("in_group")
    left_fight_times = j.get("left_fight_times")
    if str(in_group) == "0":  # 0-未报名 1-已报名
        j = requestURL(menpaiyaoqingsaibaoming)
        msg = j.get("msg")
        log.info("门派邀请赛-报名：" + msg)
    # 6.3 战斗
    if (dayOfWeek == 3 and hour >= 6) or (dayOfWeek == 1 and hour < 6) or (4 <= dayOfWeek <= 7):
        if int(left_fight_times) > 0:
            for i in range(int(left_fight_times)):
                j = requestURL(menpaiyaoqingsaizhandou)
                msg = j.get("msg")
                if str(msg).startswith("门派战书数量不足"):
                    i = i - 1
                    j = requestURL(menpaiduihuanzhanshu % {"times": "1"})
                    msg = j.get("msg")
                    log.info("门派-兑换：" + msg)
                else:
                    log.info("门派邀请赛-战斗：" + msg)


# 问鼎
def wending(level, isabandon, log):
    """
    问鼎 todo 1.指定次数
    :param level: 资源点等级 1-1级地盘 2-2级 3-3级
    :param isabandon: 占领资源点是否放弃 0-不放弃 1-放弃
    :param log:
    :return:
    """

    wendingzhuwei1 = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=tbattle&op=cheerregionbattle&faction=10215"
    wendingzhuwei2 = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=tbattle&op=cheerchampionbattle&faction=10215"
    wendinglingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=tbattle&op=drawreward"
    wendingfangqi = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=tbattle&op=abandon"
    wendingziyuan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=tbattle&op=drawreleasereward"
    wendinggongji = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=tbattle&op=occupy&id=%(id)s"

    # 助威-区域淘汰赛
    if dayOfWeek == 6 and (6 < hour < 19 or (hour == 19 and minute < 30)):
        j = requestURL(wendingzhuwei1)
        msg = j.get("msg")
        log.info("问鼎天下-区域淘汰赛助威：" + msg)
    # 助威-冠军排名赛
    if (dayOfWeek == 6 and hour >= 21) or (dayOfWeek == 7 and (hour < 19 or (hour == 19 and minute < 30))):
        j = requestURL(wendingzhuwei2)
        msg = j.get("msg")
        log.info("问鼎天下-冠军排名赛助威：" + msg)
    # 领奖
    j = requestURL(wendinglingjiang)
    msg = j.get("msg")
    if not str(msg).startswith("抱歉，上届问鼎天下您无奖励可领取") and not str(msg).startswith("你已经领取过上届问鼎天下奖励了"):
        log.info("问鼎天下-领奖：" + msg)

    if (dayOfWeek == 1 and hour >= 6) or (dayOfWeek == 6 and hour < 6) or (2 <= dayOfWeek <= 5):
        # 放弃资源点
        j = requestURL(wendingfangqi)
        msg = j.get("msg")
        log.info("问鼎天下-放弃资源点：" + msg)
        # 领资源
        j = requestURL(wendingziyuan)
        msg = j.get("msg")
        log.info("问鼎天下-收取资源：" + msg)
        # 攻击一次等级为{level}的地盘
        j = requestURL(wendinggongji % {"id": generateID(int(level))})
        msg = j.get("msg")
        log.info("问鼎天下-占领资源点：" + msg)
        if isabandon == 1:
            j = requestURL(wendingfangqi)
            msg = j.get("msg")
            log.info("问鼎天下-放弃资源点：" + msg)
        else:
            pass


def doushentarun(log, time):
    """
    斗神塔战斗线程
    :param log:
    :param time:
    :return:
    """
    doushentatiaozhan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=towerfight&type=0"
    fenxiangdoushenta = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=shareinfo&subtype=1&shareinfo=4"
    doushentazidong = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=towerfight&type=1"

    basetime = time
    if time == 8:
        basetime = 10
    log.info("斗神塔：开始挑战，并每10层分享一次")
    for i in range(1, 101):
        requestURL(doushentatiaozhan)  # 挑战
        sleep(basetime + 1)  # 等待挑战冷却
        if i >= 10 and i % 10 == 2:  # 每10层分享一次
            j = requestURL(fenxiangdoushenta)
            msg = j.get("msg")
            if str(msg).startswith("分享成功"):
                log.info("分享：" + msg)
            elif str(msg).startswith("您今日的分享次数已达上限"):
                requestURL(doushentazidong)  # 自动挑战
                log.info("分享：" + msg)
                break


def dianfengrun(log):
    """
    巅峰之战战斗线程
    :param log:
    :return:
    """
    dianfengchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=gvg&sub=0"
    dianfengzhandou = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=gvg&sub=3"

    for i in range(10):
        j = requestURL(dianfengchaxun)
        result = j.get("result")
        if str(result).startswith("-2"):
            i = i - 1
            break
        userinfo = j.get("userinfo")
        cd_time = userinfo.get("cd_time")
        if int(cd_time) == 0 or int(cd_time) >= 300:
            pass
        else:
            sleep(int(cd_time) + 1)
        j = requestURL(dianfengzhandou)
        msg = j.get("msg")
        if str(msg).startswith("恭喜你") or str(msg).startswith("很遗憾"):
            log.info("巅峰之战-挑战：" + msg)
        elif str(msg).startswith("请您先报名") or str(msg).startswith("您今天挑战次数已经达到上限") or str(msg).startswith(
                "您今天已经用完复活次数了"):
            log.info("巅峰之战-挑战：" + msg)
            break
        elif str(msg).startswith("冷却时间"):
            continue
        else:
            pass


def jiebiaorun(username, jiebiaolevel, log):
    """
    劫镖线程 todo 优化逻辑
    :param username:
    :param jiebiaolevel:
    :param log:
    :return:
    """
    biaoxingtianxiajiebiaoliebiao = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=cargo&op=3"
    biaoxingtianxiajiebiao = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=cargo&op=14&passerby_uin=%(passerby_uin)s"

    j = requestURL("https://fight.pet.qq.com/cgi-bin/petpk?cmd=rank&kind=5&other=" + str(username))
    gerenzhanli = float(j.get("total"))
    newlist = []
    count = 0
    while True:
        j = requestURL(biaoxingtianxiajiebiaoliebiao)
        result = j.get("result")
        if str(result).startswith("-1") or str(result).startswith("-2"):  # 系统繁忙，重试  fixme 应该没用了
            sleep(1)
            continue
        else:
            passerbys = j.get("passerbys")  # 获取劫镖列表
            if type(passerbys) is None:
                continue
            for item in passerbys:
                if int(item.get("aow_award")) >= int(jiebiaolevel):  # 筛选
                    # 判断战力，默认打高于战力不高于自己300的
                    j = requestURL(
                        "https://fight.pet.qq.com/cgi-bin/petpk?cmd=rank&kind=5&other=" + str(item.get("passerby_uin")))
                    zhanli = float(j.get("total"))
                    if (zhanli - gerenzhanli) <= 300:
                        newlist.append(item)
            looted_count = 3
            if len(newlist) == 0:  # 筛选后无结果，重试
                continue
            else:  # 准备劫镖
                for car in newlist:
                    j = requestURL(biaoxingtianxiajiebiao % {"passerby_uin": str(car.get("passerby_uin"))})
                    msg = j.get("msg")
                    if str(msg).startswith("这个镖车在保护期内") or str(msg).startswith(""):
                        continue;
                    drop = j.get("drop")
                    # print("镖行天下-劫镖：" + response.content.decode("gbk"))  # fixme
                    log.info("镖行天下-劫镖：" + drop)
                    looted_count = j.get("looted_count")
                    newlist.clear()
                    if int(looted_count) == 3:
                        break
            newlist.clear()
            if int(looted_count) == 3:
                break


def doushenta(log):
    """
    斗神塔
    :param log:
    :return:
    """
    doushentajieshu = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=towerfight&type=7&confirm=1"
    doushentachaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=towerfight&type=3"
    daren = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=ledouvip"

    # 1.结束斗神塔的挑战
    j = requestURL(doushentajieshu)
    msg = j.get("msg")
    if not str(msg).startswith("非法操作"):
        log.info("斗神塔结束挑战：" + msg)
    # 2.获取当日剩余挑战次数
    j = requestURL(doushentachaxun)
    day_left_times = j.get("day_left_times")  # 今日剩余免费次数
    j = requestURL(daren)
    lvl = j.get("lvl")
    if str(day_left_times).startswith("1"):
        try:
            doushenta = threading.Thread(target=doushentarun, args=(log, max(8 - int(lvl), 1)))
            doushenta.start()
        except:
            log.error("Error: 无法启动线程")
    else:
        log.info("斗神塔：今日剩余免费次数" + day_left_times)


def biaoxingtianxia(username, log, yabiaolevel=2, jiebiaolevel=2):
    """
    镖行天下
    :param username:
    :param log:
    :param yabiaolevel:
    :param jiebiaolevel:
    :return:
    """
    biaoxingtianxiayabiaojieguo = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=cargo&op=15"
    biaoxingtianxialingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=cargo&op=16"
    biaoxingtianxiaqicheng = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=cargo&op=6"
    biaoxingtianxiayabiaoxinxi = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=cargo&op=7"
    biaoxingtianxiayabiaoshuaxin = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=cargo&op=8"
    biaoxingtianxiaxinxi = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=cargo&op=0"

    # 1.先检查是否需要领奖
    j = requestURL(biaoxingtianxiayabiaojieguo)
    escort_state = j.get("escort_state")  # 0-  1-待领奖
    if str(escort_state).startswith("1"):
        j = requestURL(biaoxingtianxialingjiang)
        msg = j.get("msg")
        log.info("镖行天下-领奖：" + msg)
    # 2.押镖 yabiaolevel：0-蔡八斗  1-吕青橙  2-温良恭
    j = requestURL(biaoxingtianxiaxinxi)
    convey_count = j.get("convey_count")
    if str(convey_count).startswith("1"):  # 今日已押镖次数
        pass
    else:
        # 2.1获取当前押镖信息
        j = requestURL(biaoxingtianxiayabiaoxinxi)
        reselect_times = j.get("reselect_times")
        car_lvl = j.get("car_lvl")
        if str(reselect_times).startswith("0") or int(car_lvl) >= int(yabiaolevel):  # 没刷新次数了，直接押
            pass
        else:
            for i in range(int(reselect_times)):
                j = requestURL(biaoxingtianxiayabiaoshuaxin)  # 刷新
                msg = j.get("msg")
                car_lvl = j.get("car_lvl")
                log.info("镖行天下-押镖：" + msg)
                if (int(car_lvl) >= int(yabiaolevel)):  # 刷到了
                    break
        j = requestURL(biaoxingtianxiaqicheng)
        msg = j.get("msg")
        log.info("镖行天下-押镖：" + msg)
    # 3.劫镖
    j = requestURL(biaoxingtianxiaxinxi)
    looted_count = j.get("looted_count")
    if not str(looted_count).startswith("3"):
        try:
            jiebiao = threading.Thread(target=jiebiaorun, args=(username, jiebiaolevel, log))
            jiebiao.start()
        except:
            log.error("Error: 无法启动线程")


# （需要指定id）
def shiyongwupin(QQnum, id, log):
    """
    使用背包物品
    :param QQnum: 当前登录qq号
    :param id: 要使用物品的id
    :param log:
    :return:
    """
    beibaowupinshiyongdiannao = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=use&selfuin=%(selfuin)s&id=%(id)s"
    response = req.get(beibaowupinshiyongdiannao % {"selfuin": str(QQnum), "id": str(id)})
    html = response.content.decode("gbk")
    j = json.loads(html)
    msg = j.get("joinground")
    log.info(msg)


# todo 每日任务自动完成
def meirirenwuzhixing(header, cookie, id, log):
    if id == "13":  # 使用一次风之息,风之息id 3018
        beibaowupinshiyongshouji = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?zapp_uin=&sid=&channel=0&g_ut=1&cmd=use&id=%(id)s"
        response = req.get(beibaowupinshiyongshouji % {"id": str(3018)})
    elif id == "22":  # 好友切磋（7个人，等级差小于等于20）
        pass
    elif id == "28":  # 看5个好友资料
        gerenxinxi = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?zapp_uin=&B_UID=0&sid=&channel=0&g_ut=1&cmd=totalinfo&type=1"
        for i in range(5):
            j = requestURL(gerenxinxi)
    elif id == "29":  # 武林大会报名，默认报名电脑场
        pass
    elif id == "34":  # 挑战四姑娘(id=15)
        pass
    elif id == "36":  # 挑战俊猴王(id=12)
        pass
    elif id == "61":  # 斗一次结拜好友
        pass
    elif id == "67":  # 挑战3次陌生人
        pass
    elif id == "74":  # 斗神塔1次
        pass
    elif id == "78":  # 历练3次
        pass
    elif id == "86":  # 挑战程管(id=16)
        pass
    elif id == "88":  # 挑战马大师(id=14)
        pass
    elif id == "89":  # 挑战邪神(id=19)
        pass
    elif id == "103":  # 传功6次
        pass
    elif id == "104":  # 分享3次
        pass
    elif id == "107":  # 幻境
        pass
    elif id == "108":  # 十二宫
        pass
    elif id == "109":  # 完成押镖1次
        pass
    elif id == "111":  # 劫镖1次（无论成功失败）
        pass
    elif id == "112":  # 劫镖3次（无论成功失败）
        pass
    elif id == "114":  # 专精强化1次（符文石）
        pass
    elif id == "115":  # 专精强化1次（寒铁）
        pass
    elif id == "11":  # 强化一次徽章
        pass
    else:  # 未知任务id
        pass


def wulinmengzhu(id, log):
    """
    武林盟主
    :param id: 报名武林盟主的类型  1-黄金 2-白银 3-青铜
    :return:
    """
    wulinmengzhuchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=wlmz&op=view_index"
    wulinmengzhulingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=wlmz&round_id=%(round_id)s&op=get_award&section_id=%(section_id)s"
    wulinemenzhubaoming = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=wlmz&op=signup&ground_id=%(ground_id)s"
    wulinmengzhujiangcaixuanze = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=wlmz&op=guess_up&index=%(index)s"
    wulinmengzhujiangcaiqueren = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=wlmz&op=comfirm"
    # 竞猜领奖
    j = requestURL(wulinmengzhuchaxun)
    # print(j)
    award_info = j.get("award_info")
    rest_time = j.get("rest_time")
    if award_info != "":
        section_id = award_info[0].get("section_id")
        round_id = award_info[0].get("round_id")
        j = requestURL(wulinmengzhulingjiang % {"round_id": str(round_id), "section_id": section_id})
        msg = j.get("msg")
        log.info("武林盟主领奖：" + msg)
    if not str(rest_time.get("is_final")).startswith("1"):
        if dayOfWeek in [1, 3, 5] and 12 <= hour < 24:
            # 报名
            j = requestURL(wulinemenzhubaoming % {"ground_id": str(id)})
            msg = j.get("msg")
            log.info("武林盟主报名：" + msg)
        elif dayOfWeek in [2, 4, 6] and 12 <= hour < 21:
            # 竞猜选择
            for i in range(8):
                j = requestURL(wulinmengzhujiangcaixuanze % {"index": str(i)})
            # 竞猜确认
            j = requestURL(wulinmengzhujiangcaiqueren)
            msg = j.get("msg")
            log.info("武林盟主竞猜：" + msg)


def yuanzhengjun(log):
    """
    帮派远征军
    :param log:
    :return:
    """
    yuanzhengjundaoyuchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factionarmy&op=viewIndex&island_id=%(island_id)s"  # 0-4
    yuanzhengjunlingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factionarmy&op=getPointAward&point_id=%(point_id)s"  # 0-14
    yuanzhengjundaoyulingjinag = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factionarmy&op=getIslandAward&island_id=%(island_id)s"  # 0-4

    # https://fight.pet.qq.com/cgi-bin/petpk?cmd=factionarmy&point_id=0&op=getPointAward
    for i in range(5):
        j = requestURL(yuanzhengjundaoyuchaxun % {"island_id": str(i)})
        fightInfo = j.get("fightInfo")
        if type(fightInfo) is None or fightInfo == "":
            i = i - 1
            continue
        islandAwardStatus = fightInfo.get("islandAwardStatus")  # 0-不可领取  1-待领奖  2-已领
        islandInfo = fightInfo.get("islandInfo")
        for ii in range(3):
            island0 = islandInfo[ii]
            if island0.get("awardStatus") == "1":
                # 领奖
                j = requestURL(yuanzhengjunlingjiang % {"point_id": str(i * 3 + ii)})
                msg = j.get("msg")
                log.info("帮派远征军：岛屿" + str(i + 1) + "-" + str(ii + 1) + "领奖" + msg)
        if str(islandAwardStatus) == str(1):
            j = requestURL(yuanzhengjundaoyulingjinag % {"island_id": str(i)})
            msg = j.get("msg")
            log.info("帮派远征军：岛屿" + str(i + 1) + "-" + "4领奖 " + msg)


def liumenhuiwu(log):
    """
    六门会武
    :param log:
    :return:
    """
    huiwuzhuweichaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sectmelee&op=showcheer"
    huiwuzhuwei = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sectmelee&sect=1003&op=cheer"
    huiwushilian = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sectmelee&op=dotraining"
    huiwulingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sectmelee&op=drawreward"

    # todo 加个判断，等级小于40不执行次功能
    # 助威 周一早6点~周五早6点
    j = requestURL(huiwuzhuweichaxun)  # 默认助威丐帮
    cheer_sect = j.get("cheer_sect")
    if (dayOfWeek == 1 and hour >= 6) or (dayOfWeek == 5 and hour < 6) or dayOfWeek in [2, 3, 4] or str(
            cheer_sect).startswith("0"):
        j = requestURL(huiwuzhuwei)
        msg = j.get("msg")
        if not str(msg).startswith("本周已为门派助威"):
            log.info("六门会武-助威：" + msg)
    if dayOfWeek in [1, 6, 7]:
        j = requestURL(huiwulingjiang)
        msg = j.get("msg")
        log.info("会武-领奖：" + msg)
    # 会武试炼
    # todo 判断试炼书够不够，不够自动换1个
    # 挑战
    for i in range(20):
        j = requestURL(huiwushilian)
        msg = j.get("msg")
        log.info("六门会武-试炼：" + msg)
        if str(msg).startswith("你已达今日挑战上限") or str(msg).startswith("当前时段不能进行该操作"):
            break


def huiliu(log, qqnum="-1"):
    """
    回流好友召回
    :param log:
    :param qqnum: 不填默认为-1，随机召唤
    :return:
    """
    huiliuchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=callback&subtype=3"
    huiliulibao1 = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=callback&subtype=6&gift=2"
    huiliulibao2 = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=callback&subtype=6&gift=3"
    huiliuzhaohuan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=callback&subtype=4&opuin=%(opuin)s"

    j = requestURL(huiliuchaxun)
    msg = j.get("msg")
    # if str(msg).startswith("很抱歉，系统繁忙"):
    #     return
    daycallnum = j.get("daycallnum")
    canbecall = j.get("canbecall")
    bind = j.get("bind")

    if len(bind) > 0:
        j = requestURL(huiliulibao1)
        msg = j.get("msg")
        log.info("回流-热心助人礼包：" + msg)
        j = requestURL(huiliulibao2)
        msg = j.get("msg")
        log.info("回流-豪情快意礼包：" + msg)

    times = 3 - int(daycallnum)

    if int(times) == 0:
        pass
    elif len(canbecall) > 0:
        if qqnum == "-1":
            qqnum = canbecall[0].get("uin")
        # 开始召回
        for i in range(times):
            j = requestURL(huiliuzhaohuan % {"opuin": str(qqnum)})
            msg = j.get("msg")
            log.info("回流召回：" + msg)
    else:
        pass


# bossID
# 2-乐斗教主  3-乐斗帅帅  4-乐斗姜公  5-乐斗月璇姐姐  6-乐斗源大侠  7-乐斗菜菜 9-乐斗剑君
# 10-羊魔王  11-月敏妹妹  12-俊猴王  13-大色魔  14-马大师  15-四姑娘 16-乐斗程管 17-山贼
# 18-强盗  19-邪神畅哥  31-守将程关大侠（地盘） 32-守将朱仁大侠（地盘）  33-金毛鹅王 150-苏醒醒
# 151-新手小王子  152-曾小三  153-盗圣  154-羊叫兽  155-一灯大师  156-黄药师
def tiaozhanboss(log, qqnum):
    """
    挑战boss
    :param log:
    :param qqnum:
    :return:
    """
    chakanhaoyou = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=view&kind=1&sub=1&selfuin=%(selfuin)s"
    zhandou = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fight&puin=%(puin)s"
    ledoujiluchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=view&kind=2&sub=1&selfuin=%(selfuin)s"
    chakanbangyou = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=viewmember"
    zhandoubangpai = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fight&uin=%(uin)s"
    chakanjiebaixialv = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?zapp_uin=&sid=&channel=0&g_ut=1&cmd=viewxialv"
    zhandoujiebaixialvboss = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?zapp_uin=&sid=&channel=0&g_ut=1&cmd=fight&B_UID=%(B_UID)s"

    # 获取好友列表
    j = requestURL(chakanhaoyou % {"selfuin": str(qqnum)})
    info = j.get("info")
    for i in range(10):
        enable = info[i].get("enable")
        uin = info[i].get("uin")
        if str(enable).startswith("1") and int(uin) < 10000:
            requestURL(zhandou % {"puin": str(uin)})  # 返回信息里貌似没有记录，去战斗记录里找第一条信息作为结果
            j = requestURL(ledoujiluchaxun % {"selfuin": str(qqnum)})
            ledoujilu = j.get("info")
            if len(ledoujilu) > 0:
                desc = ledoujilu[0].get("desc")
                log.info("乐斗-挑战boss：" + desc)
    # 帮派boss todo 判断有没有帮派
    j = requestURL(chakanbangyou)
    msg = j.get("msg")
    if str(msg).startswith("很抱歉"):
        pass
    else:
        level = j.get("level")
        bosslist = j.get("list")
        for i in range(1, int(level) + 1):
            fight = bosslist[i].get("fight")
            if str(fight).startswith("1"):
                uin = bosslist[i].get("uin")
                requestURL(zhandoubangpai % {"uin": str(uin)})
                j = requestURL(ledoujiluchaxun % {"selfuin": str(qqnum)})
                info = j.get("info")
                if len(info) > 0:
                    desc = info[0].get("desc")
                    log.info("乐斗-挑战boss：" + desc)
    # 结拜boss,侠侣boss
    response = req.get(chakanjiebaixialv)
    html = response.content.decode("utf-8")
    # pattern = re.compile('B_UID=[1-9]\d*>乐斗')
    pattern = re.compile('B_UID=[1-9]\d*&amp;page=&amp;type=10">乐斗')
    bossList = pattern.findall(html)
    bossList = list(set(bossList))

    newlist = []
    for i in bossList:
        id = str(i).replace("B_UID=", "").replace("&amp;page=&amp;type=10\">乐斗", "")
        if int(id) < 10000:
            newlist.append(id)
    if len(newlist) > 0:
        for i in newlist:
            response = req.get(zhandoujiebaixialvboss % {"B_UID": str(i)})
            html = response.content.decode("utf-8")
            if "使用规则" in str(html):
                continue
            j = requestURL(ledoujiluchaxun % {"selfuin": str(qqnum)})
            info = j.get("info")
            if len(info) > 0:
                desc = info[0].get("desc")
                log.info("乐斗-挑战boss：" + desc)


def shengri(log):
    """
    生日
    :param log:
    :return:
    """
    shengrichaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=birthday"
    shengrilingjiang1 = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=birthday&op=getfreepresent"
    shengrilingjiang2 = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=birthday&op=getwishespresent"
    shengrishuaxin = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=birthday&op=getrandomfriends"
    shengriyouhaodulibao = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=birthday&op=getwishdegreepresent"
    shengrifasongzhufu = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=birthday&op=sendwishes&receiver=%(receiver)s"

    # 1.生日祝福 todo 判断生日领奖领过没
    j = requestURL(shengrichaxun)  # 查询在不在生日周
    in_event = j.get("in_event")
    received_wishes_num = j.get("received_wishes_num")  # 当前收到的祝福数
    wishes_required = j.get("wishes_required")  # 生日领奖所需祝福数
    wish_degree = j.get("wish_degree")  # 当前友好度
    wish_degree_required = j.get("wish_degree_required")  # 领奖所需友好度
    num = int(wish_degree_required) - int(wish_degree)
    # 生日期间领奖
    if str(in_event).startswith("1"):
        j = requestURL(shengrilingjiang1)
        msg = j.get("msg")
        log.info("生日-专属大礼：" + msg)
        if int(received_wishes_num) >= int(wishes_required):  # 生日的祝福礼包（符文石+幸运石+黄金卷轴）
            j = requestURL(shengrilingjiang2)
            msg = j.get("msg")
            log.info("生日-祝福大礼：" + msg)
    # 日常好友生日祝福
    newlist = []
    for i in range(10):
        j = requestURL(shengrishuaxin)  # 刷新列表
        friends = j.get("friends")
        for friend in friends:
            can_send_wishes = friend.get("can_send_wishes")
            if str(can_send_wishes).startswith("1"):
                newlist.append(friend.get("uin"))
    wishlist = list(set(newlist))
    for qqnum in wishlist:
        # 送祝福
        if num == 0:
            j = requestURL(shengriyouhaodulibao)
            msg = j.get("msg")
            log.info("生日-友好度礼包：" + msg)
            num = wish_degree_required
        else:
            j = requestURL(shengrifasongzhufu % {"receiver": str(qqnum)})
            msg = j.get("msg")
            log.info("生日-祝福：" + msg)
            if str(msg).startswith("成功发送祝福"):
                num = num - 1


def meirijiangli(log):
    """
    每日奖励
    :param log:
    :return:
    """
    meirijianglichakan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=dailygift"
    meirijianglilingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=dailygift&op=draw&key=%(key)s"

    j = requestURL(meirijianglichakan)
    meridian = j.get("meridian")  # 传功符礼包
    login = j.get("login")  # 每日礼包
    daren = j.get("daren")  # 达人礼包
    wuzitianshu = j.get("wuzitianshu")  # 无字天书礼包
    for item in [meridian, login, daren, wuzitianshu]:
        if str(item.get("status")).startswith("0"):
            j = requestURL(meirijianglilingjiang % {"key": str(item.get("key"))})
            msg = j.get("msg")
            log.info("每日奖励:" + msg)


def doudouyueka(username, log):  # todo html页面解析
    """
    斗豆月卡领奖
    :param username:
    :param log:
    :return:
    """
    yuakachaxun = "https://dld.qzapp.z.qq.com/qpet/cgi-bin/phonepk?zapp_uin=&B_UID=0&sid=&channel=0&g_ut=1&cmd=monthcard"
    yuakalingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=use&id=3645&selfuin=%(selfuin)s"

    response = req.get(yuakachaxun)
    html = response.content.decode("utf-8")
    if (str(html).find("还未开通斗豆月卡")) == -1:
        j = requestURL(yuakalingjiang % {"selfuin": str(username)})
        msg = j.get("msg")
        log.info("斗豆月卡：" + msg)


# todo 微端


def yaoqing(log):
    """
    邀请
    :param log:
    :return:
    """
    yaoqingchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sundyact&subtype=4"
    yaoqingfenxiang1 = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sundyact&subtype=6&inviteNum=5"
    yaoqingfenxiang2 = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sundyact&subtype=6&inviteeKind=1&inviteNum=1"
    yaoqingchoujiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=sundyact&subtype=5"

    j = requestURL(yaoqingchaxun)
    inviteNum = j.get("inviteNum")
    inviteQQGroupNum = j.get("inviteQQGroupNum")
    if int(inviteNum) < 5:
        j = requestURL(yaoqingfenxiang1)
        # msg = j.get("msg")
        # log.info("邀请-分享：" + msg)
    if int(inviteQQGroupNum) < 1:
        j = requestURL(yaoqingfenxiang2)
        # msg = j.get("msg")
        # log.info("邀请-分享：" + msg)
    for i in range(2):
        j = requestURL(yaoqingchoujiang)
        msg = j.get("msg")
        if not str(msg).startswith("今天已经抽过2次奖了"):
            log.info("邀请-抽奖：" + msg)


def liwu(log):
    """
    免费礼物（优先回赠）
    :param log:
    :return:
    """
    liwuchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=exchangegifts&op=msg"
    liwushouqu = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=exchangegifts&op=receive&id=%(id)s"
    liwuhuizeng = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=exchangegifts&op=sendback&recipient=%(recipient)s"
    liwuzengsong = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=exchangegifts&op=reply&id=%(id)s"

    j = requestURL(liwuchaxun)
    notifications = j.get("notifications")
    giftin = []  # 待收取
    giftout = []  # 待赠送
    for item in notifications:
        if str(item.get("type")).startswith("1"):
            giftin.append(item)
        else:
            giftout.append(item)
    for item in giftin:
        j = requestURL(liwushouqu % {"id": str(item.get("id"))})  # 收取
        if j == None:
            continue
        # print(item.get("id"))
        msg = j.get("msg")
        if str(msg).startswith("找不到对应的消息"):
            continue
        elif str(msg).startswith("今日收取次数已达上限"):
            break
        else:
            log.info("礼物-收取：" + msg)
            j = requestURL(liwuhuizeng % {"recipient": str(item.get("uin"))})  # 优先回赠
            msg = j.get("msg")
            log.info("礼物-回赠：" + msg)
    for item in giftout:
        j = requestURL(liwuzengsong % {"id": str(item.get("id"))})  # 赠送`
        if j is None:
            continue
        msg = j.get("msg")
        if str(msg).startswith("今天已经给他送过礼物啦"):
            continue
        elif str(msg).startswith("今日赠送次数已达上限"):
            break
        else:
            log.info("礼物-赠送：" + msg)


def shanghui(log):
    """
    商会 todo 1.自定义交易兑换列表 2.硬币低于某个数值后不兑换
    :param log:
    :return:
    """
    shanghuibaoku = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_corp&op=0&page=1"
    shanghuilingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_corp&op=3&type=%(type)s&giftId=%(giftId)s"
    shanghuijiaoyichaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_corp&op=1"
    shanghuijiaoyi = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_corp&op=4&type=%(type)s&goods_id=%(goods_id)s"
    shanghuiduihuanchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_corp&op=2"
    shanghuiduihuan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=fac_corp&op=5&type_id=%(type_id)s"

    # 1.领奖
    while True:
        j = requestURL(shanghuibaoku)
        giftInfo = j.get("giftInfo")
        if type(giftInfo) == None:
            continue
        if len(giftInfo) == 0:
            break
        gifilist = []
        for item in giftInfo:
            gifttype = item.get("type")
            giftid = item.get("giftId")
            j = requestURL(shanghuilingjiang % {"type": str(gifttype), "giftId": giftid})
            msg = j.get("msg")
            if str("msg").startswith("入帮24小时才能领取商会礼包"):
                break
            log.info("商会-领奖：" + msg)
    # 2.交易
    j = requestURL(shanghuijiaoyichaxun)
    tradeInfo = j.get("tradeInfo")
    for item in tradeInfo:
        if str(item.get("isTraded")).startswith("0"):
            if int(item.get("goodsId")) in [3374, 3487]:
                gifttype = item.get("type")
                goodsid = item.get("goodsId")
                j = requestURL(shanghuijiaoyi % {"type": str(gifttype), "goods_id": goodsid})
                msg = j.get("msg")
                log.info("商会-交易：" + msg)
    # 3.兑换
    j = requestURL(shanghuiduihuanchaxun)
    coinNum = j.get("coinNum")
    if int(coinNum) <= 1000:
        #print("buduihuan")
        pass
    else:
        exchangeInfo = j.get("exchangeInfo")
        for item in exchangeInfo:
            if str(item.get("isExchanged")).startswith("0") and int(coinNum) >= int(item.get("coinNum")):
                if int(item.get("goodsId")) in []:
                    # 兑换
                    j = requestURL(shanghuiduihuan % {"type_id": str(item.get("typeId"))})
                    msg = j.get("msg")
                    log.info("商会-兑换：" + msg)
                    coinNum = coinNum - item.get("coinNum")
                else:
                    # print("不在交易列表")
                    pass


def bangpairenwu(username, log):
    """
    帮派任务
    :param username:
    :param log:
    :return:
    """
    global flag
    bangpairenwuchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factiontask&sub=1"
    bangpairenwuwancheng = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factiontask&taskid=%(taskid)s&sub=2"

    j = requestURL(bangpairenwuchaxun)
    tasklist = j.get("array")
    tasklisttodo = []
    tasklistdone = []
    for task in tasklist:
        if str(task.get("state")).startswith("0"):
            tasklisttodo.append(task)
        elif str(task.get("state")).startswith("1"):
            tasklistdone.append(task)
        else:
            continue
    for task in tasklisttodo:
        if int(task.get("id")) == 1:
            # 帮派供奉:向守护神任意供奉1个物品。(供奉还魂丹)
            gongfeng(log, 3089)
        elif int(task.get("id")) == 8 or int(task.get("id")) == 9:
            # 帮派修炼:进行一/三次帮派修炼
            a = 1 if int(task.get("id"))==8 else 3
            for i in range(1, a+1):
                flag = bangpaixiulian(log)
                if flag:
                    continue
        elif int(task.get("id")) == 10:
            # 查看矿洞:进入矿洞界面，查看本帮派矿洞详情
            kuangdongchakan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factionmine"
            requestURL(kuangdongchakan)
        elif int(task.get("id")) == 11:
            # 查看帮贡:点击贡献度查询，查看自己在帮派中的排名
            gongxianchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factiontask&sub=3"
            requestURL(gongxianchaxun)
        elif int(task.get("id")) == 12 or int(task.get("id")) == 14:
            # 查看帮战:进入帮派战争界面，查看本帮赛区战况。/进入帮派战争界面，查看本帮赛区的总冠军战况
            bangzhanchakan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=facwarrsp&id=1"
            requestURL(bangzhanchakan)
        elif int(task.get("id")) == 13:
            # 粮草掠夺:进入粮草掠夺战界面，查看本帮战斗状况。
            liangcaochakan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=forage_war"
            requestURL(liangcaochakan)
        elif int(task.get("id")) == 15:
            # 加速贡献:使用1次贡献药水。
            shiyongwupin(username, "3038", log)
        elif int(task.get("id")) == 16:
            # 查看要闻:点击帮派要闻，查看帮派最近动态。
            bangpaiyaowen = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factionstaff&page=1"
            requestURL(bangpaiyaowen)
        tasklistdone.append(task)
    for task in tasklistdone:
        j = requestURL(bangpairenwuwancheng % {"taskid": task.get("id")})
        msg = j.get("msg")
        log.info("帮派-任务：" + msg)


def bangpaixiulian(log):
    """
    帮派技能修炼
    :param log:
    :return:
    """
    bangpaixiulian = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factiontrain&type=2&id=%(id)s&times=1"
    bangpaijinengchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=factiontrain&type=1"
    j = requestURL(bangpaijinengchaxun)
    skilllist = j.get("array")
    for skill in skilllist:
        j = requestURL(bangpaixiulian % {"id": str(skill.get("id"))})
        msg = j.get("msg")
        if str(msg).startswith("技能经验增加"):
            # arr = j.get("array")
            # index = int(list.index(skill))
            # skill = arr[index]
            log.info("帮派-修炼：修炼" + str(skill.get("name")) + "," + str(msg) + str(skill.get("cur_lvl_exp")))
            return True
    return False


def bangpaijitan(log):
    """
    帮派祭坛 todo 通关领奖
    :param log:
    :return:
    """
    jitanchakan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=altar"
    jitanzhuanpan = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=altar&op=spinwheel"
    showtarget = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=altar&op=showspecialtargets"
    rob = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=altar&id=%(id)s&op=rob"
    steal = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=altar&id=%(id)s&op=steal"
    jitanlingjiang = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=altar&op=drawreward"

    j = requestURL(jitanchakan)
    last_reward_points = j.get("last_reward_points")
    if int(last_reward_points)>0:
        j = requestURL(jitanlingjiang)
        msg = j.get("msg")
        log.info("祭坛-领奖：" + msg)
    while True:
        j = requestURL(jitanchakan)
        left_free_wheel_times = j.get("left_free_wheel_times")
        if int(left_free_wheel_times) == 0:
            break
        print("祭坛剩余免费次数：" + left_free_wheel_times)
        j = requestURL(jitanzhuanpan)
        action_id = j.get("action_id")
        if str(action_id) in ["1000", "1001", "1002", "1005", "1006", "1007", "1008"]:
            msg = j.get("msg")
            log.info("帮派祭坛-转盘：" + str(msg))
        elif str(action_id) == "1003":
            j = requestURL(showtarget)
            randomfac = j.get("random_faction")
            enemieslist = j.get("enemies")
            revengelist = j.get("revenge_targets")
            steallist = enemieslist + revengelist
            steallist.append(randomfac)
            # 宣战>复仇>随机
            for enemy in steallist:
                j = requestURL(rob % {"id": str(enemy.get("id"))})
                msg = j.get("msg")
                if str(msg).startswith("该帮派正处于保护中"):
                    continue
                else:
                    log.info("帮派祭坛-掠夺：" + str(msg))
                    break
        elif str(action_id) == "1004":
            j = requestURL(showtarget)
            randomfac = j.get("random_faction")
            enemieslist = j.get("enemies")
            revengelist = j.get("revenge_targets")
            steallist = enemieslist + revengelist
            steallist.append(randomfac)
            # 宣战>复仇>随机
            for enemy in steallist:
                j = requestURL(steal % {"id": str(enemy.get("id"))})
                msg = j.get("msg")
                if str(msg).startswith("该帮派正处于保护中"):
                    continue
                else:
                    log.info("帮派祭坛-偷取：" + str(msg))
                    break
        else:
            continue

def jingjichang(log):
    """
    竞技场 todo 1.挑战 2.赛季末领奖 3.自动兑换 4.排行榜奖励
    :param log:
    :return:
    """
    jingjichangchaxun = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=arena"
    jingjichaangmeirijiangli = "https://fight.pet.qq.com/cgi-bin/petpk?cmd=arena&op=dailyreward"

    j = requestURL(jingjichangchaxun)
    rest_time = j.get("rest_time")
    left_free_times = j.get("left_free_times")
    if int(rest_time) > 0:
        #挑战
        pass


        #领奖
        j = requestURL(jingjichangchaxun)
        can_draw_daily_reward = j.get("can_draw_daily_reward")
        if str(can_draw_daily_reward) == "1":
            j = requestURL(jingjichaangmeirijiangli)
            msg = j.get("msg")
            log.info("竞技场-领奖：" + msg)



def sendmsg():
    pass




def parser(response):
    """
    解析返回的json字符串
    :param response:
    :return:
    """
    html = response.content.decode("gbk", 'ignore')
    html = html.replace("\\n","").replace("\\","")
    j = json.loads(html)
    return j


def requestURL(url):
    """
    PC端请求接口，返回json
    :param url:
    :return:
    """
    for times in range(10):
        response = req.get(url)
        retjson = parser(response)
        # -5:登录失效 -2:系统繁忙  0:正常
        if str(retjson.get("result")).startswith("-5"):
            print("登陆校验失败")  # 未登录，退出
            sys.exit()
        elif str(retjson.get("result")).startswith("-2"):
            # 请求过快了
            sleep(1)
            continue
        else:
            return retjson
