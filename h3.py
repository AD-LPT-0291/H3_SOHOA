#!/usr/bin/env python3
from pyA20.gpio import gpio #x
from pyA20.gpio import port #x
import time
from time import sleep
import os
from threading import Timer
import subprocess
import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import urllib
import url
import khaibao
import requests
import socket
import configparser
import re
import signal
import psutil
import alsaaudio
gpio.init()

led_status = 16 #chan 16
watchdog = 13 # chan 13
led_connect = 15 # chan 11
kich_modul4g = 14 # chan 18
phim_wifi = 3
on_off = 0 # chan 50
up = 1 #chan 51
down = 2 #chan 52

prev_on_off = False
prev_up = False
prev_down = False

pressed = False
start_time = 0
#kich_nguon_sac = 16 # chan 18
gpio.setcfg(led_status, gpio.OUTPUT)
gpio.setcfg(watchdog, gpio.OUTPUT)
gpio.setcfg(led_connect, gpio.OUTPUT)
gpio.setcfg(kich_modul4g, gpio.OUTPUT)
gpio.setcfg(phim_wifi, gpio.INPUT)   #Configure PE11 as input
gpio.setcfg(on_off, gpio.INPUT)   #Configure PE11 as input
gpio.setcfg(up, gpio.INPUT)   #Configure PE11 as input
gpio.setcfg(down, gpio.INPUT)   #Configure PE11 as input

gpio.pullup(down, gpio.PULLDOWN)    #Enable pull-down
gpio.pullup(up, gpio.PULLDOWN)    #Enable pull-down
gpio.pullup(phim_wifi, gpio.PULLDOWN)    #Enable pull-down
gpio.pullup(on_off, gpio.PULLDOWN)    #Enable pull-down
gpio.output(kich_modul4g, 1)
gpio.output(watchdog, 0)

darkice_process = ''
darkice_cmd = ['darkice', '-c', '/etc/darkice.cfg']
# Đường dẫn đến tệp cấu hình của Darkice
CONFIG_FILE = "/etc/darkice.cfg"
# Tạo đối tượng ConfigParser
config = configparser.ConfigParser()
config.optionxform = lambda option: option


######### khai bao domain ##########
domainMqtt = url.domainMqtt
portMqtt = url.portMqtt
domainXacnhanketnoi = url.domainXacnhanketnoi
domainLogbantin = url.domainLogbantin
domainPing = url.domainPing
domainXacnhanketnoilai = url.domainXacnhanketnoilai

######## khai bao dia chi mqtt #####
id = khaibao.id
updatecode = khaibao.updatecode
trangthaiketnoi = khaibao.trangthaiketnoi
trangthaiplay = khaibao.trangthaiplay
trangthaivolume = khaibao.trangthaivolume
xacnhanketnoi = khaibao.xacnhanketnoi
dieukhienvolume = khaibao.dieukhienvolume
dieukhienplay = khaibao.dieukhienplay
yeucauguidulieu = khaibao.yeucauguidulieu
reset = khaibao.reset

####################################
phienban = "V1.0.0"
wifi = False
start = False
loiketnoi = 0
mabantinnhan = ''
kiemtraPlay = 0
demKiemtra = 0
data = ''
maxacthuc = ''
guidulieu = 0
ledConnectStatus = False
watchdogStatus = False
demRestartModul3g = 0
chedoRetartModul3g = False
demLoicallApiPing = 0
trangthaiguiApi = None
mangdangdung = ''
### khai bao nhap nhay wifi 
ledConnectStatus = 0
demnhapnhay = 0
demdung = 0
demnhanphim = 0
##### khai bao data do toc do mang speedtest #####
speedtest_upload = ''
speedtest_download = ''
speedtest_ping = ''
speedtest_ping_jitter = ''
### khai bao data ping ########
urldangphat = ''
tenchuongtrinh = ''
kieunguon = ''
thoiluong = ''
tennoidung = ''
diachingoidung = ''
kieuphat = ''
nguoitao = ''
taikhoantao = ''
# khai bao data api tinh #
userName = ''
password = '' 
madiaban = ''
tendiaban = ''
imel = ''
tenthietbi = ""
lat = ''
lng = ''
Status = "false"
khoaguidulieu = False
domainLoginTinh = ''
domainPingTinh = ''
domainLogTinh = ''
Video = {"Index":"0", "Time": "", "MediaName": "", "AudioName": "", "Path": "", "Level": 0  }

########
class RepeatedTimer(object):
  def __init__(self, interval, function, *args, **kwargs):
    self._timer     = None
    self.interval   = interval
    self.function   = function
    self.args       = args
    self.kwargs     = kwargs
    self.is_running = False
    self.start()
  def _run(self):
    self.is_running = False
    self.start()
    self.function(*self.args, **self.kwargs)
  def start(self):
    if not self.is_running:
      self._timer = Timer(self.interval, self._run)
      self._timer.start()
      self.is_running = True
  def stop(self):
    self._timer.cancel()
    self.is_running = False
#########
######### get dia chi ip ###################
def get_ip_address():
 ip_address = ''
 s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
 s.connect(("8.8.8.8",80))
 ip_address = s.getsockname()[0]
 s.close()
 return ip_address

############# ham call api xac nhan ket noi #################
def api_xacnhanketnoi(data):
  global start, trangthaiguiApi, userName, password, domainLoginTinh, domainPingTinh, domainLogTinh, imel, tenthietbi, madiaban, tendiaban, lat, lng, Status, Video, khoaguidulieu
  try:
    responsePingtest = requests.post(domainXacnhanketnoi, json = data)
    jsonResponse = responsePingtest.json()
    if(jsonResponse['success'] == True):
      # dieu khien volume #
      setVolume(jsonResponse['data']['data']['volume'])
       # Đọc nội dung của tệp cấu hình
      config.read(CONFIG_FILE)
      # Thay đổi giá trị input
      config.set("input", "device", jsonResponse['data']['data']['deviceinput'])
      config.set("input", "channel", jsonResponse['data']['data']['channel'])
      config.set("icecast2-0", "bitrate", jsonResponse['data']['data']['bitrate'])
      config.set("icecast2-0", "server", jsonResponse['data']['data']['serverstream'])
      config.set("icecast2-0", "port", jsonResponse['data']['data']['portstream'])
      config.set("icecast2-0", "password", jsonResponse['data']['data']['password'])
      config.set("icecast2-0", "name", jsonResponse['data']['data']['nameStream'])
      config.set("icecast2-0", "mountPoint", jsonResponse['data']['data']['mountPoint'])
      # Ghi lại nội dung vào tệp cấu hình
      with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)
      # dieu khien play #
      if(jsonResponse['data']['data']['statusPlay'] == 'play'):   
        if(jsonResponse['data']['data']['deviceId'] == id):  
         for proc in subprocess.Popen(['pgrep', '-f', 'darkice'], stdout=subprocess.PIPE).stdout:
            pid = int(proc.decode())
            os.kill(pid, signal.SIGTERM)   
         start_darkice() 
        
      else:
        stop_darkice()
       
  except:
    print('loi xac nhan ket noi')
  # get_speedtest()
#############################################################

############ ham gui nhat ky ban tin ve tinh ################
def api_nhatkybantinTinh(data):
  global Status, Video
  Status = "true"     
  #gui nhat ky ban tin ve tinh#
  volume = subprocess.check_output("mpc volume", shell=True ).decode("utf-8")
  volume = volume[8:]
  volume = volume[:-1]
  seconds = time.time()
  dataLichsuApi = {
    'Imei': imel,
    'DeviceName': tenthietbi,
    'Provider': data['Provider'],
    'MediaId': data['MediaId'],
    'SourceId': data['SourceId'],
    'SourceName': data['SourceName'],
    'DestinationId': data['DestinationId'],
    'DestinationName': data['DestinationName'],
    'Title': data['Title'],
    'Description': "",
    'Body': data['Body'],
    'IsExternal': int(data['IsExternal']) ,
    'ExternalSource': data['ExternalSource'],
    'Volume': volume[:-1],
    'PAState': "",
    'Priority': {
      'id': int(data['Priority']['id']),
      'value': data['Priority']['value']
    },
    'Category': {
      'id': int(data['Category']['id']) ,
      'value': data['Category']['value']
    },
    'ContentType': { 
      'id': 3, 
      'value': data['ContentType']['value'] },
    'Author': {
      'id': data['Author']['id'],
      'Fullname': data['Author']['Fullname'],
      'Username': data['Author']['Username'],
      'Avatar': data['Author']['Avatar'],
      'Email': data['Author']['Email']
    },
    'StartTime': int(seconds),
    'CreateDate': int(data['CreateDate']),
    'Duration': data['Duration']
  }
  try:
    responseLogbantinTinh = requests.post(domainLoginTinh, json = {'Username':userName, 'Password':password}, headers={'Content-Type': "application/json", 'Accept': "application/json"})
    datajsonResponseLog = responseLogbantinTinh.json()
    if(datajsonResponseLog['Message'] == 'Success'): 
      headers = {'Authorization': "Bearer {}".format(datajsonResponseLog["Token"])}
      responseLog = requests.post(domainLogTinh, json = dataLichsuApi, headers=headers, timeout=5)
    # responseLog = requests.post(domainLogTinh, json = dataLichsuApi)
  except:
    print('loi gui log ban tin ve tinh')
#############################################################  

############# ping data ve tinh 30s #########################
def pingTinh():
  global trangthaiguiApi, userName, password, domainLoginTinh, domainPingTinh, domainLogTinh, imel, tenthietbi, madiaban, tendiaban, lat, lng, Status, Video, khoaguidulieu
  # test
  if not khoaguidulieu:
    if trangthaiguiApi == None or userName == '':
      try:
        data = {
          'id': id
        }
        responseXacnhan = requests.post(domainXacnhanketnoilai, json= data)
        jsonResponse = responseXacnhan.json()
        if jsonResponse['success'] == True:
          domainLoginTinh = jsonResponse['data']['domainLogin']
          domainPingTinh = jsonResponse['data']['domainPing']
          domainLogTinh = jsonResponse['data']['domainLog']
          userName = jsonResponse['data']['userName']
          password = jsonResponse['data']['password']
          imel = jsonResponse['data']['imel']
          tenthietbi = jsonResponse['data']['deviceName']
          madiaban = jsonResponse['data']['DestinationID']
          tendiaban = jsonResponse['data']['DestinationName']
          lat = jsonResponse['data']['lat']
          lng = jsonResponse['data']['lng']
          if jsonResponse['data']['statusApi'] == True:
            trangthaiguiApi = True
          else:
            trangthaiguiApi = False
            khoaguidulieu = True
            pingApiTinh.stop()
      except:
        print('loi call api xac nhan ket noi lai')
  if trangthaiguiApi:
    # seconds = time.time()
    # volume = subprocess.check_output("mpc volume", shell=True )
    # volume = volume[8:]
    # volume = volume[:-1]
    # ping = {
    #   'AppName': 'IpRadio',
    #   'LogType': 'Report',
    #   'Provider': 'Gtechdn',
    #   'Imei': imel,
    #   'DeviceName': tenthietbi,
    #   'Lat': float(lat),
    #   'Lng': float(lng),
    #   'Volume': volume[:-1],
    #   'ConnectionId': '',
    #   'DestinationID': madiaban,
    #   'DestinationName': tendiaban,
    #   'NetworkInfo':'4G',
    #   'StartTime': int(seconds),
    #   'Status': Status,
    #   'Version': '2.2.1',
    #   'Video': json.dumps(Video),    
    # }     
    # try:
    #   responsePing = requests.post(domainPingTinh, json = ping)
    # except:
    #   print('loi call api ping tinh ')
      try:
        response = requests.post(domainLoginTinh, json = {'Username':userName, 'Password':password}, headers={'Content-Type': "application/json", 'Accept': "application/json"})
        jsonResponse = response.json()
        trangthai = jsonResponse['Message']
        if trangthai == 'Success':
          Token = jsonResponse["Token"]  
          seconds = time.time()
          # volume #
          volume = subprocess.check_output("mpc volume", shell=True ).decode("utf-8")
          volume = volume[8:]
          volume = volume[:-1]
          ping = {
            'AppName': 'IpRadio',
            'LogType': 'Report',
            'Provider': 'Gtechdn',
            'Imei': imel,
            'DeviceName': tenthietbi,
            'Lat': float(lat),
            'Lng': float(lng),
            'Volume': volume[:-1],
            'ConnectionId': '',
            'DestinationID': madiaban,
            'DestinationName': tendiaban,
            'NetworkInfo':'4G',
            'StartTime': int(seconds),
            'Status': Status,
            'Version': '2.3.0',
            'Video': json.dumps(Video),    
          }     
          headers = {'Authorization': "Bearer {}".format(Token)}   
          responsePing = requests.post(domainPingTinh, json = ping, headers=headers, timeout=5)
      except:
        print('loi call api ping tinh ')
#############################################################

################ ping server 20s ############################
def pingServer():
  global Video, urldangphat, tenchuongtrinh, kieunguon, thoiluong, tennoidung, diachingoidung, kieuphat, nguoitao, taikhoantao, demLoicallApiPing, loiketnoi, kiemtraPlay, led_status, demKiemtra, mabantinnhan, trangthaiplay
  if(loiketnoi  == 10):
    os.system("(sudo systemctl restart myapp.service)")
  # volume #
  try:
    volume = subprocess.check_output("mpc volume", shell=True ).decode("utf-8")
    volume = volume[8:]
    volume = volume[:-1]
    # trang thai play #
    if get_darkice_status_ping() == True:
      station_status = "play"
      gpio.output(led_status,1)
    else:
      station_status = "stop"
      gpio.output(led_status,0)
    dataPing = {
      'url': urldangphat,
      'id': id,
      'trangthai': station_status,   
      'tenchuongtrinh': tenchuongtrinh,
      'kieunguon': kieunguon,
      'thoiluong': thoiluong,
      'tennoidung': tennoidung,
      'diachingoidung': diachingoidung,
      'kieuphat': kieuphat,
      'nguoitao': nguoitao,
      'taikhoantao': taikhoantao,
      'trangthaiplay': trangthaiplay,
    }
    
    responsePingtest = requests.post(domainPing, json = dataPing, timeout=5)
    trave = responsePingtest.json()
    if(trave['data'] != ''):
      if(trave['data']['statusPlay'] == 'play'):       
        os.system("mpc clear")
        os.system("mpc stop")
        os.system("mpc add '" + trave['data']['url'] + "'")
        os.system("mpc play") 
        Video = {"Index":"0", "Time": trave['data']['duration'], "MediaName": "", "AudioName": trave['data']['audioName'], "Path": trave['data']['path'], "Level": trave['data']['Level']  }
        volume = subprocess.check_output("mpc volume", shell=True ).decode("utf-8")
        volume = volume[8:]
        volume = volume[:-1]
        # trang thai play #
        station = subprocess.check_output("mpc current", shell=True ).decode("utf-8")
        lines=station.split(":")
        length = len(lines)      
        if length==1:
          line1 = lines[0]
          line1 = line1[:-1]
          line2 = "No additional info: "
        else:
          line1 = lines[0]
          line2 = lines[1]
        line2 = line2[:42]
        line2 = line2[:-1]
        #trap no station data
        if line1 =="":
          line2 = "Press PLAY or REFRESH"
          station_status = "stop"           
        else:
          station_status = "play"         
        urldangphat = trave['data']['url']
        tenchuongtrinh = trave['data']['title']
        kieunguon = trave['data']['sourceType']
        thoiluong = trave['data']['duration']
        tennoidung = trave['data']['audioName']
        diachingoidung = trave['data']['path']
        kieuphat = trave['data']['playType']
        nguoitao = trave['data']['AuthorFullname']
        taikhoantao = trave['data']['AuthorUsername']
        kiemtraPlay = 1       
        demKiemtra = 0
        gpio.output(led_status,1)
        client.publish(trangthaiplay,station_status)
        loiketnoi +=1
      # gui log ve server #
        thoigianphat = time.time()
        if(mabantinnhan != trave['data']['mabantin']):
          dataLog = {
          'urldangphat': trave['data']['url'],
          'id': id,  
          'tenchuongtrinh': trave['data']['title'],
          'kieunguon': trave['data']['sourceType'],
          'thoiluong': trave['data']['duration'],
          'tennoidung': trave['data']['audioName'],
          'diachingoidung': trave['data']['path'],
          'kieuphat': trave['data']['playType'],
          'nguoitao': trave['data']['AuthorFullname'],
          'taikhoantao': trave['data']['AuthorUsername'],
          'thoigianphat': int(thoigianphat),
          'volume': volume,
        
          }   
          responsePingtest = requests.post(domainLogbantin, json = dataLog, timeout=5)    
          mabantinnhan = trave['data']['mabantin']
      if(trave['data']['statusPlay'] == 'stop'):
        os.system("mpc clear")
        os.system("mpc stop")
        volume = subprocess.check_output("mpc volume", shell=True ).decode("utf-8")
        volume = volume[8:]
        volume = volume[:-1]
        # trang thai play #
        station = subprocess.check_output("mpc current", shell=True ).decode("utf-8")
        lines=station.split(":")
        length = len(lines)      
        if length==1:
          line1 = lines[0]
          line1 = line1[:-1]
          line2 = "No additional info: "
        else:
          line1 = lines[0]
          line2 = lines[1]
        line2 = line2[:42]
        line2 = line2[:-1]
        #trap no station data
        if line1 =="":
          line2 = "Press PLAY or REFRESH"
          station_status = "stop"   
        else:
          station_status = "play" 
        urldangphat = ''
        tenchuongtrinh = ''
        kieunguon = ''
        thoiluong = ''
        tennoidung = ''
        diachingoidung = ''
        kieuphat = ''
        nguoitao = ''
        taikhoantao = ''
        gpio.output(led_status,0)
        client.publish(trangthaiplay,station_status)
        Video = {"Index":"0", "Time": "", "MediaName": "", "AudioName": "", "Path": "", "Level": 0  }
        mabantinnhan = ''
        loiketnoi +=1
        kiemtraPlay = 0
     
    demLoicallApiPing = 0
    nhapnhatLedConnectCallApiloi.stop()
    gpio.output(led_connect,1) 
    
  except:
    if demLoicallApiPing < 40:
      demLoicallApiPing+=1
    if demLoicallApiPing == 1:
      nhapnhatLedConnect.stop()
      nhapnhatLedConnectCallApiloi.start()
      os.system("mpc stop")
    if demLoicallApiPing == 20:
       retartModul3g()  
    if demLoicallApiPing == 38:
      os.system("(sudo systemctl restart myapp.service)")
    # if not run_main:
    #   nhapnhatLedConnectCallApiloi.stop()
    print('loi ping 20s ve server ')
#############################################################
def start_darkice():
    global  start,  trangthaiplay, led_status
    # start darkice stream
    subprocess.Popen(['darkice'])
    if get_darkice_status() == True:
      client.publish(trangthaiplay,"play")
      gpio.output(led_status,True)
      start = True
def stop_darkice():
    global  start, trangthaiplay, led_status
    # stop darkice stream
    client.publish(trangthaiplay,"stop")
    gpio.output(led_status,False)
    start = False
    for proc in subprocess.Popen(['pgrep', '-f', 'darkice'], stdout=subprocess.PIPE).stdout:
        pid = int(proc.decode())
        os.kill(pid, signal.SIGTERM)

def get_darkice_status_ping():
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'status'])
        except psutil.NoSuchProcess:
            pass
        else:
            if 'darkice' in pinfo['name']:
                return True
    return False

def get_darkice_status():
    cmd = 'pgrep darkice'
    try:
        result = subprocess.check_output(cmd, shell=True)
        pid = int(result.strip())
        return True
    except subprocess.CalledProcessError:
        return False

############# kiem tra trang thai play ######################
def kiemtraTrangthaiPlay():
  print(get_darkice_status())
  
#############################################################

##############nhap nhay led phat wifi #######################
def led_nhapnhaywifi():
    global ledConnectStatus, demnhapnhay, demdung
    if(demnhapnhay < 4):
     gpio.output(led_connect,not ledConnectStatus)
     ledConnectStatus = not ledConnectStatus
     demnhapnhay+=1
     demdung=0
    if(demnhapnhay == 4):
     demdung+=1
    if(demdung == 16):
     demnhapnhay=0

############### Blinl led connect ###########################
def ledConnectNhapnhay():
    global ledConnectStatus
    gpio.output(led_connect,not ledConnectStatus) 
    ledConnectStatus = not ledConnectStatus
#############################################################

########## ham kich sung modul watchdog #####################
def watchdogStart():
  global watchdogStatus
  gpio.output(watchdog,not watchdogStatus)
  watchdogStatus = not watchdogStatus
############################################################

###### led connect nhap nhay canh bao call Api loi #########
def ledConnectNhapnhayLoiCallApi():
    global ledConnectStatus
    gpio.output(led_connect,not ledConnectStatus) 
    ledConnectStatus = not ledConnectStatus
############################################################

###################### ham play ############################
def play(data):
  global Video, kiemtraPlay, demKiemtra, trangthaiplay, led_status, urldangphat, tenchuongtrinh, kieunguon, thoiluong, tennoidung, diachingoidung, kieuphat, nguoitao, taikhoantao
  time.sleep(1)
  try:
    os.system("mpc clear")
    os.system("mpc add '" + data['url'] + "'")
    os.system("mpc play")   
    kiemtraPlay = 1       
    demKiemtra = 0
    station = subprocess.check_output("mpc current", shell=True ).decode("utf-8")
    lines=station.split(":")
    length = len(lines) 
    if length==1:
      line1 = lines[0]
      line1 = line1[:-1]
      line2 = "No additional info: "
    else:
      line1 = lines[0]
      line2 = lines[1]
    line2 = line2[:42]
    line2 = line2[:-1]
    #trap no station data
    if line1 =="":
      line2 = "Press PLAY or REFRESH"
      station_status = "stop"   
    else:
      station_status = "play"     
    client.publish(trangthaiplay,station_status)
    gpio.output(led_status,1)
   
    # gui log ban tin ve server #
    urldangphat = data['url']
    tenchuongtrinh = data['title']
    kieunguon = data['sourceType']
    thoiluong = data['duration']
    tennoidung = data['audioName']
    diachingoidung = data['path']
    kieuphat = data['playType']
    nguoitao = data['AuthorFullname']
    taikhoantao = data['AuthorUsername']
    # volume #
    volume = subprocess.check_output("mpc volume", shell=True ).decode("utf-8")
    volume = volume[8:]
    volume = volume[:-1]
    ## luu log ban tin
    thoigianphat = time.time()
    dataLog = {
      'urldangphat': urldangphat,
      'id': id,  
      'tenchuongtrinh': tenchuongtrinh,
      'kieunguon': kieunguon,
      'thoiluong': thoiluong,
      'tennoidung': tennoidung,
      'diachingoidung': diachingoidung,
      'kieuphat': kieuphat,
      'nguoitao': nguoitao,
      'taikhoantao': taikhoantao,
      'thoigianphat': int(thoigianphat) ,
      'volume': volume,
     
    }
    try:
      responsePingtest = requests.post(domainLogbantin, json = dataLog, timeout=4)
    except:
      print('loi call api log ban tin ve server ')
    ### ping ban tin dang phat ve server ###
    dataPing = {
      'url': urldangphat,
      'id': id,
      'trangthai': station_status,   
      'tenchuongtrinh': tenchuongtrinh,
      'kieunguon': kieunguon,
      'thoiluong': thoiluong,
      'tennoidung': tennoidung,
      'diachingoidung': diachingoidung,
      'kieuphat': kieuphat,
      'nguoitao': nguoitao,
      'taikhoantao': taikhoantao,
      'trangthaiplay': trangthaiplay,
    }
  
    responsePingtest = requests.post(domainPing, json = dataPing, timeout=5)
  except:
    print('loi ping ban tin dang phat play ve server ')
############################################################

#################### ham stop ##############################
def stop():
  global Status, Video,  kiemtraPlay, trangthaiplay, led_status, urldangphat, tenchuongtrinh, kieunguon, thoiluong, tennoidung, diachingoidung, kieuphat, nguoitao, taikhoantao
  try:
    os.system("mpc clear")
    os.system("mpc stop")          
    gpio.output(led_status,0)
    kiemtraPlay = 0
    station = subprocess.check_output("mpc current", shell=True ).decode("utf-8")
    lines=station.split(":")
    length = len(lines) 
    if length==1:
      line1 = lines[0]
      line1 = line1[:-1]
      line2 = "No additional info: "
    else:
      line1 = lines[0]
      line2 = lines[1]
    line2 = line2[:42]
    line2 = line2[:-1]
  #trap no station data
    if line1 =="":
      line2 = "Press PLAY or REFRESH"
      station_status = "stop"   
    else:
      station_status = "play" 
    client.publish(trangthaiplay,station_status)
    urldangphat = ''
    tenchuongtrinh = ''
    kieunguon = ''
    thoiluong = ''
    tennoidung = ''
    diachingoidung = ''
    kieuphat = ''
    nguoitao = ''
    taikhoantao = ''

    Status = "false"
    Video = {"Index":"0", "Time": "", "MediaName": "", "AudioName": "", "Path": "", "Level": 0  }
    ### ping ban tin dang phat ve server ###
    dataPing = {
      'url': urldangphat,
      'id': id,
      'trangthai': station_status,   
      'tenchuongtrinh': tenchuongtrinh,
      'kieunguon': kieunguon,
      'thoiluong': thoiluong,
      'tennoidung': tennoidung,
      'diachingoidung': diachingoidung,
      'kieuphat': kieuphat,
      'nguoitao': nguoitao,
      'taikhoantao': taikhoantao,
      'trangthaiplay': trangthaiplay,
    }
    
    responsePingtest = requests.post(domainPing, json = dataPing, timeout=5)
  except:
    print('loi ping ban tin dang phat stop ve server ')
############################################################

################# ham dieu khien volume ####################
def setVolume(volume):
  # Khởi tạo mixer
  mixer = alsaaudio.Mixer('Mic1 Boost', cardindex=0)
  # Đặt âm lượng
  mixer.setvolume(int(volume))
  current_volume = mixer.getvolume()[0]
############################################################

############ khoi dong lai modul 3g ########################
def retartModul3g():
    global demRestartModul3g
    gpio.output(kich_modul4g,0) 
    time.sleep(5)
    gpio.output(kich_modul4g,1) 
    demRestartModul3g = 0
############################################################


############### on_disconnect ##############################
def on_disconnect(client, userdata, flags, rc=0):
    m="DisConnected flags"+"result code "+str(rc)+"client_id  "
    print(m)
    client.connected_flag=False
############################################################

#################### connect MQTT ##########################
def on_connect(client, userdata, flags, rc):
    global demLoicallApiPing, yeucauguidulieu, updatecode, dieukhienvolume, dieukhienplay, maxacthuc, chedoRetartModul3g, demRestartModul3g, demLoicallApiPing
    if rc==0:
        print("connected OK Returned code=",rc)
        demLoicallApiPing = 0
        chedoRetartModul3g = False
        demRestartModul3g = 0      
        #Flag to indicate success
        client.subscribe(dieukhienvolume) 
        client.subscribe(updatecode)
        client.subscribe(dieukhienplay)
        client.subscribe(yeucauguidulieu)
        client.subscribe(reset)
        client.connected_flag=True
        nhapnhatLedConnect.stop()
        nhapnhatLedConnectCallApiloi.stop()
        gpio.output(led_connect,True) 
        """ call API xac nhan ket noi """
       # ip = requests.get('https://api.ipify.org').text
        dataXacnhanketnoi = {
          'xacnhanketnoi': xacnhanketnoi,
          'ip': get_ip_address(),
          'phienban': phienban,   
        }
        api_xacnhanketnoi(dataXacnhanketnoi)           
    else:
        print("Bad connection Returned code=",rc)
        client.bad_connection_flag=True
###########################################################

############### ham hien thi log ##########################
def on_log(client, userdata, level, buf):
    print("log: ",buf)
###########################################################

########### nhan tin nhan tu broker #######################
def on_message(client, userdata, msg):
    global start,  darkice_process,  kiemtraPlay, updatecode, dieukhienvolume, dieukhienplay, demKiemtra, guidulieu, yeucauguidulieu, userName, password, domainPing, imel, tenthietbi, madiaban, tendiaban, lat, lng, Status, Video, khoaguidulieu
    themsg = msg.payload.decode("utf-8")
    topic = msg.topic
    #### nhan lenh tu server ####
    #### update code ####
    if topic == updatecode:
      try:
        data = themsg.split() 
        if data[0] == id:
          os.system("(cd /home/dung/sohoa && git pull https://phamdung1211:'"+ data[1] + "'@bitbucket.org/phamdung1211/sohoa.git && sudo reboot)")
      except:
        print('loi')
    #### khoi dong lai thiet bi ####
    if topic == reset:
      if themsg == id:
        os.system("(sudo reboot)")
    #### dieu chinh am luong ####
    if topic == dieukhienvolume: 
       try:
        data = json.loads(themsg)
        if data['deviceId'] == id:
          setVolume(data['volume'])
       except:
        print('loi')
    #### play ban tin  ####
    if topic == dieukhienplay: 
      try:
        data = json.loads(themsg)  
        if data['status'] == "updateconfig":
          if data['deviceId'] ==  id:
            # Đọc nội dung của tệp cấu hình
            config.read(CONFIG_FILE)
            # Thay đổi giá trị input
            config.set("input", "device", data['deviceinput'])
            config.set("input", "channel", data['channel'])
            config.set("icecast2-0", "bitrate", data['bitrate'])
            config.set("icecast2-0", "server", data['serverstream'])
            config.set("icecast2-0", "port", data['portstream'])
            config.set("icecast2-0", "password", data['password'])
            config.set("icecast2-0", "name", data['nameStream'])
            config.set("icecast2-0", "mountPoint", data['mountPoint'])
            if(data['statusstream'] == True):
              stop_darkice()
            # Ghi lại nội dung vào tệp cấu hình
            with open(CONFIG_FILE, "w") as configfile:
              config.write(configfile)
            if(data['statusstream'] == True):
              start_darkice()
             
        if data['status'] == "play":
          if data['deviceId'] ==  id:           
             start_darkice()   
              
        # #### stop luong ####
        if data['status'] == "stop":
          if data['deviceId'] == id:
            stop_darkice()
            
      except:
        print('loi')
    ### gui log ban tin ve tinh ####
    if topic == yeucauguidulieu:
      try:
        data = json.loads(themsg) 
        if(data['command'] == 'play'):
          Video = {"Index":"0", "Time": data['Duration'], "MediaName": "", "AudioName": data['AudioName'], "Path": data['Path'], "Level": data['Level']}
          if trangthaiguiApi:
            api_nhatkybantinTinh(data)     
        ##### console #########
        if(data['command'] == 'console'):
          if(data['id'] == id):
            os.system(data['data'])
      except:
        print('loi')
###########################################################
CLEAN_SESSION=False
#broker="iot.eclipse.org" #use cloud broker
client = mqtt.Client()    #create new instance
#client.on_log=on_log #client logging
mqtt.Client.connected_flag=False #create flags
mqtt.Client.bad_connection_flag=False #
mqtt.Client.retry_count=0 #
client.on_connect=on_connect        #attach function to callback
client.will_set("device/offline", payload=id, qos=1, retain=False)
client.on_disconnect=on_disconnect
client.on_message = on_message
nhapnhatLedConnect = RepeatedTimer(1, ledConnectNhapnhay)
nhapnhatLedConnectCallApiloi = RepeatedTimer(0.2, ledConnectNhapnhayLoiCallApi)
nhapnhatLedConnectCallApiloi.stop()
#kiemtraPlay = RepeatedTimer(1, kiemtraTrangthaiPlay)
callApipingServer = RepeatedTimer(20, pingServer)
pingApiTinh = RepeatedTimer(30, pingTinh)
watchdog_start = RepeatedTimer(1, watchdogStart)
nhapnhay_wifi = RepeatedTimer(0.15, led_nhapnhaywifi)
nhapnhay_wifi.stop()
# speedtest_start = RepeatedTimer(60, get_speedtest)
#pwmLed = RepeatedTimer(1, pwm_led)
run_main=False
run_flag=True

while run_flag:

    while not client.connected_flag and client.retry_count<3:
        count=0 
        run_main=False
        try:
            print("connecting ",domainMqtt)         
            client.connect(domainMqtt,portMqtt,60)      
            break #break from while loop
        except:           
            print("connection attempt failed will retry")         
            # nhapnhatLedConnect.start()
            # nhapnhatLedConnectCallApiloi.stop()
            client.retry_count+=1         
            if(client.retry_count == 2):
              retartModul3g()
              print('khoi dong lai modul lan dau...')
            #if client.retry_count>3:
                #print('thoat')
                #run_flag=False
    if not run_main:   
        client.loop_start()
        while True:
            if client.connected_flag: #wait for connack
                client.retry_count=0 #reset counter
                run_main=True
                break
            # if count>6 or client.bad_connection_flag: #don't wait forever
            #   demRestartModul3g+=1
            #   if demRestartModul3g >= 900:                  
            #     print('reset lai modul 3g..')
            #     retartModul3g()                  
            # time.sleep(1)
            count+=1
    if run_main:
        try:
          time.sleep(1)
        except(KeyboardInterrupt):
            print("keyboard Interrupt so ending")
            #run_flag=False
    while True:
     
      current_time = time.time()
      current_on_off = gpio.input(on_off) # # Lấy trạng thái hiện tại của phím
      current_up = gpio.input(up)
      current_down = gpio.input(down)
      # if current_on_off != prev_on_off and current_on_off:
      #   print('ok on_off')
      if gpio.input(phim_wifi):
        if not pressed:
            # Nếu phím được nhấn lần đầu tiên
            pressed = True
            start_time = current_time
            wifi = not wifi
      else:
        if pressed:
            # Nếu phím được nhả ra sau khi được giữ
            pressed = False
            elapsed_time = current_time - start_time
            if elapsed_time >= 3:             
                # Nếu thời gian giữ phím lớn hơn hoặc bằng 3 giây
                if wifi == True:               
                  nhapnhatLedConnectCallApiloi.stop()
                  nhapnhay_wifi.start()
                  os.system("sudo systemctl start myappserver.service")
                  os.system("sudo systemctl start nginx")
                  os.system("sudo service hostapd start")
                if wifi == False:
                  nhapnhay_wifi.stop()
                  gpio.output(led_connect,1) 
                  demnhanphim = 0
                  os.system("sudo systemctl stop myappserver.service")
                  os.system("sudo systemctl stop nginx")
                  os.system("sudo service hostapd stop")
            else:
                # Nếu thời gian giữ phím nhỏ hơn 5 giây
                if start == True: 
                  stop_darkice()
                else:
                  start_darkice() 
                  
      if current_up != prev_up and current_up:
        print('ok up')
      if current_down != prev_down and current_down:
        print('ok down')
      prev_on_off = current_on_off
      prev_up = current_up
      prev_down = current_down
      time.sleep(0.1)  # Tạm dừng 0.1 giây
print("quitting")
    
    # client.disconnect()
# client.loop_stop()
