# -*- coding: utf-8 -*-
"""
sleepSpeak_07.py
2019

10/27　夜目が覚めた際に、揺らすと時間を教えてくれる。
10/29　　　 電源オンとともにスタートするようにする
        　 IPを固定にする。
        ◯ フリフリを続けるとシャットダウンするようにする。
        ◯ raspberrypt 1model A+でWifiドングルをつけて動くとよい
11/05　　　6時と23時にしゃべる。
11/13     macからラズパイのpiにあるsleep_start.shを叩くと、起6:04動する。
11/14  03 twitterにつぶやく
11/17      バグ修正　0時に死んでいた
11/20　　　カウントをやめてsleepで対応
11/25     一度も時間を確認しなかった日の対応
11/30     ツイッターに二度呟くのを止める
12/01  05 やはり二度ベルを鳴らす....　色々確認したが、不明　様子見
        　げんいんはわからないが、出ないような対策をして効いたみたい。
2020/03/04
        06  ログ記録追加
2020/05/02
        07  朝のしゃべりを追加。天気、気温、休日
2020/05/17  曜日を追加
2020/05/24  土日は休日と喋らない


"""

import time
import subprocess
import sys
import datetime
import RPi.GPIO as GPIO
from nobu_LIB import Lib_twitter
import requests

###################log print#####################
# 自身のプログラム名からログファイル名を作る
import sys
args = sys.argv
logFileName = args[0].strip(".py") + "_log.csv"
# ログファイルにプログラム起動時間を記録
import csv
# 日本語文字化けするので、Shift_jisやめてみた。
f = open(logFileName, 'a')
csvWriter = csv.writer(f)
csvWriter.writerow([datetime.datetime.now(),'  program start!!'])
f.close()
#----------------------------------------------
def log_print(msg1="",msg2="",msg3=""):
    # エラーメッセージなどをプリントする際に、ログファイルも作る
    # ３つまでのデータに対応
    print(msg1,msg2,msg3)
    # f = open(logFileName, 'a',encoding="Shift_jis") 
    # 日本語文字化けするので、Shift_jisやめてみた。
    f = open(logFileName, 'a')
    csvWriter = csv.writer(f)
    csvWriter.writerow([datetime.datetime.now(),msg1,msg2,msg3])
    f.close()
################################################

# set GPIO 0 as switch pin
Tilt_Switch = 26
# チルトスイッチの電源がリード線の関係で3.3Vピンに接続しにくかったので、
# 信号線から電源を取ることにしました。いいのか?
plusPin = 13

def setup():
    GPIO.setwarnings(False)
    #set the gpio modes to BCM numbering
    GPIO.setmode(GPIO.BCM)
    #set plusPin's mode to output,and initial level to High(3.3V)
    GPIO.setup(plusPin,GPIO.OUT,initial=GPIO.HIGH)
    GPIO.setup(Tilt_Switch,GPIO.IN)

def speakPrint(say_word):
    log_print(say_word)
    subprocess.run('sh ~/julius/jsay_mei.sh ' + say_word,shell=True)
    return

def timeSpeak():
    dt_now = datetime.datetime.now()
    speak_word = "今の時刻は、" + str(dt_now.hour) + "時" + str(dt_now.minute) +  "分です。" 
    speakPrint(speak_word)

    minute = dt_now.minute
    if minute <10 :
        said_time =  str(dt_now.hour) + ":0" + str(dt_now.minute) 
    else:
        said_time =  str(dt_now.hour) + ":" + str(dt_now.minute) 
    print("-------------------------------------")
    return said_time

def youbiSpeak():
    dt_now = datetime.datetime.now()
    yobi = ["月曜日です","火曜日です","水曜日です","木曜日です","金曜日です","土曜日です","日曜日です"]
    today_youbi = yobi[dt_now.weekday()]
    speakPrint(today_youbi)
    return

def dateSpeak():
    dt_now = datetime.datetime.now()
    speak_word = "今日は、" + str(dt_now.month) + "月" + str(dt_now.day) +  "日で、" 
    speakPrint(speak_word)
    return 

def checkEnd():
    speakPrint('2秒のちに、このまま揺らさないと、プログラムを停止します。')
    # 現在の状態をセット
    if (GPIO.input(Tilt_Switch)):
        Tilt_ = 'on'
    else:
        Tilt_= 'off'
    log_print(Tilt_)
    time.sleep(1)
    # チルトスイッチをみて、状態が変わっていれば、Tilt_timerを0とする。
    Tilt_timer = 10
    for i in range(40):
        if (GPIO.input(Tilt_Switch)):
            if Tilt_ == 'off':Tilt_timer = 0
            Tilt_ = 'on'
        else:
            if Tilt_ == 'on':Tilt_timer = 0
            Tilt_= 'off'
        time.sleep(0.1)
    log_print(Tilt_,Tilt_timer)
    if Tilt_timer == 10:
        speakPrint('揺れなかったので、プログラムを終了します。')
        raise ValueError("stop mode")
        # シャットダウンする場合は変更する。
    else:
        speakPrint('揺れたので、プログラムを続行します。')

def weatherSpeak():
    print("-------------今日の　天気・気温----------------")
    #天気
    url = "http://weather.livedoor.com/forecast/webservice/json/v1"
    payload = {"city":"270000"}
    tenki_data = requests.get(url, params=payload).json()

    try:
        tenki_say1 = "今日の天気は" + tenki_data["forecasts"][0]["telop"] + "です。"
    except:
        print("今日の天気情報はありません")
        tenki_say1 = ""
    try:
        tenki_say2 = "気温は" + tenki_data["forecasts"][0]["temperature"]["max"]["celsius"] + "度でしょう。"
        print(tenki_say2)
    except:
        print("今日の気温情報はありません")
        tenki_say2 = ""

    if tenki_say1 != "" : 
        speakPrint(tenki_say1)

    if tenki_say2 != "" : 
        speakPrint(tenki_say2)
    print("-------------------------------------")
    return

def main():
    Tilt_ = 'off'
    # 降り続けて止めるためのカウンター
    # 一旦しゃべった後、3-6秒くらいの間に振ると止まる
    Tilt_timer = 10
    yobi = ["月","火","水","木","金","土","日"]
    said_time = ""
    twitter_cnt = 0
    speakPrint('スリープスピークを始めます。')

    while True:
        # チルトスイッチをみて、状態が変わっていれば、現在時刻を喋る。
        if (GPIO.input(Tilt_Switch)):
            if Tilt_ == 'off':
                if Tilt_timer >2 and Tilt_timer <9 :checkEnd()
                said_time = said_time + " " + timeSpeak()
                Tilt_timer = 0
            Tilt_ = 'on'
        else:
            if Tilt_ == 'on':
                if Tilt_timer >2 and Tilt_timer <9 :checkEnd()
                said_time = said_time + " " + timeSpeak()
                Tilt_timer = 0
            Tilt_= 'off'
        time.sleep(1)
        Tilt_timer += 1
        print(Tilt_timer,end='', flush=True)

        # テスト用時間設定
        test_H = 10
        test_M = 9

        dt_now = datetime.datetime.now()
        if yobi[dt_now.weekday()] in ["月","火","水","木","金"]:
        # if yobi[dt_now.weekday()] in ["月","火","水","木","金","土","日"]:
        
            # 平日の朝　6時に時を告げる
            if dt_now.hour == 6 and dt_now.minute == 0:
            # if dt_now.hour == test_H and dt_now.minute == test_M:
                    speakPrint('おはよう')
                    dateSpeak()
                    youbiSpeak()
                    timeSpeak()
                    time.sleep(55)
                    
            # 平日の朝　6時20分に もう一度時を告げる     
            if dt_now.hour == 6 and dt_now.minute == 20:
            # if dt_now.hour == test_H and dt_now.minute == test_M + 2:
                    speakPrint('おはよう')
                    timeSpeak()
                    weatherSpeak()
                    time.sleep(55)

            # 平日の朝　6時40分に もう一度時を告げる     
            if dt_now.hour == 6 and dt_now.minute == 40:
            # if dt_now.hour == test_H and dt_now.minute == test_M + 4:
                    speakPrint('おはよう')
                    dateSpeak()
                    youbiSpeak()
                    timeSpeak()
                    weatherSpeak()
                    # 休日判定
                    # http://s-proj.com/utils/holiday.html ←説明ページ
                    url = "http://s-proj.com/utils/checkHoliday.php"
                    response = requests.get(url)
                    print('休日判定結果=',response.text)
                    if 'holiday' in response.text:
                        speakPrint('ちなみに今日は休日の様です。')
                    else:
                        speakPrint('そろそろ起きませんか?')
                    time.sleep(55)

        # 土日の朝　7時00分に時を告げる     
        if dt_now.hour == 7 and dt_now.minute == 0:
        # if dt_now.hour == test_H and dt_now.minute == test_M + 6:
            if yobi[dt_now.weekday()] in ["土","日"]:
            # if yobi[dt_now.weekday()] in ["月","火","水","木","金","土","日"]:
                speakPrint('おはよう')
                dateSpeak()
                youbiSpeak()
                timeSpeak()
                weatherSpeak()
                # 休日判定
                # http://s-proj.com/utils/holiday.html ←説明ページ
                url = "http://s-proj.com/utils/checkHoliday.php"
                response = requests.get(url)
                print('休日判定結果=',response.text)
                if 'holiday' in response.text:
                    # speakPrint('ちなみに今日は休日です。')
                    pass
                else:
                    speakPrint('土日なのに休日判定がおかしいです。')
                time.sleep(55)

        # 毎朝　7時40分に 一度だけツイッターで昨夜の状況をつぶやく
        if dt_now.hour == 7 and dt_now.minute == 40:
            print()
            print('1-',said_time)
            said_time = said_time[1:]
            print('2-',said_time)
            said_time_ = said_time.split()
            print('3-',said_time_)
            if said_time != "":
                said_time_ = (sorted(set(said_time_), key=said_time_.index))
                print('4-',said_time_)
                said_time_all = ""
                for j in range(len(said_time_)):
                    said_time_all = said_time_all + " " + str(said_time_[j])
            else:
                said_time_all = "昨夜は快眠だったか外泊かで、時刻確認はありませんでした。"
            log_print('5-',said_time_all)
            msg = '昨夜の結果 ' + said_time_all
            if twitter_cnt == 0:
                log_print("twitter=",msg)
                Lib_twitter.twitter(msg)
                speakPrint('ツイッターに昨夜の結果を投稿しました。')
                twitter_cnt = 1
            said_time_.clear()
            print('6-',said_time)
            print('6-',said_time_)
            print('6-',said_time_all)
            print('6-',msg)
            time.sleep(70)
            dt_now = datetime.datetime.now()

        # 23時に時を告げる
        if dt_now.hour == 23 and dt_now.minute == 0:
            timeSpeak()
            time.sleep(55)

        # 23時15分
        if dt_now.hour == 23 and dt_now.minute == 15:
            timeSpeak()
            speakPrint('そろそろ寝ませんか')
            time.sleep(55)

        # 日替わり時にカウンターをリセット
        if dt_now.hour == 0 and dt_now.minute ==0:
            print(said_time)
            said_time = ""
            time.sleep(55)
            twitter_cnt = 0
        
#define a destroy function for clean up everything after the script finished
def destroy_shutdown():
    #release resource
    GPIO.setup(plusPin,GPIO.OUT,initial=GPIO.LOW)
    GPIO.cleanup()
    # シャットダウンする場合は変更する。
    subprocess.run('sudo shutdown now',shell=True)

def destroy_stop():
    #release resource
    GPIO.setup(plusPin,GPIO.OUT,initial=GPIO.LOW)
    GPIO.cleanup()

if __name__ == '__main__':
    setup()
    try:
        main()
    #when 'Ctrl+C' is pressed,child program destroy() will be executed.
    except KeyboardInterrupt:
        log_print("key入力がありましたので、プログラム停止" )
        destroy_stop()
    except ValueError as e:
        log_print(e)
        destroy_shutdown()
