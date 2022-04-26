from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from datetime import datetime,timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException
import time
import requests
import pytz
import pause
import ddddocr
import os
import base64

def web_driver_init(): 
    options = Options()

    options.add_argument('--headless')
    options.add_argument("window-size=1440,1900")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')


    web_driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', chrome_options=options)

    return web_driver

def login(web_driver,account,password):
    web_driver.get("https://ntupesc.ntu.edu.tw/facilities/Default.aspx")

    login_tab_element = web_driver.find_element_by_xpath("//span[@id='__tab_ctl00_ContentPlaceHolder1_tcTab_TabPanel3']/font")
    login_tab_element.click()

    account_element = web_driver.find_element_by_id("ctl00_ContentPlaceHolder1_tcTab_TabPanel3_txtMemberID")
    account_element.send_keys(account)

    password_element = web_driver.find_element_by_id("ctl00_ContentPlaceHolder1_tcTab_TabPanel3_txtPassword")
    password_element.send_keys(password)

    web_driver.find_element_by_id("ctl00_ContentPlaceHolder1_tcTab_TabPanel3_btnLogin").click()

def readyBookPage(web_driver,parameter):
    court_code = parameter['court_code']
    start_time_code = parameter['start_time_code']
    end_time_code = parameter['end_time_code']
    date_code = parameter['date_code']

    book_url = 'https://ntupesc.ntu.edu.tw/facilities/PlaceOrderFrm.aspx?buildingSeq=MAA1&placeSeq={}&dateLst=&sTime={}&eTime={}&section=MQA1&date={}&week=MwA1'.format(court_code,start_time_code,end_time_code,date_code)
    print(book_url)
    web_driver.get(book_url)
    # web_driver.get("https://ntupesc.ntu.edu.tw/facilities/PlaceGrd.aspx?nFlag=0&placeSeq=2&dateLst=2022/4/25")

    # # tr 2 = 8點
    # book_button_element = web_driver.find_element_by_xpath("//table[@id='ctl00_ContentPlaceHolder1_tab1']/tbody/tr[2]/td[4]/img")
    # book_button_element.click()


    place_num_element = web_driver.find_element_by_id("ctl00_ContentPlaceHolder1_txtPlaceNum")
    place_num_element.clear()
    place_num_element.send_keys(parameter['place_number'])
 
    insertCaptcha(web_driver)

def captchImageResponse(cookies):
    my_cookies = {}
    for cookie in cookies:
        my_cookies[cookie['name']] = cookie['value']
    request = requests.get('https://ntupesc.ntu.edu.tw/facilities/ValidateCode.aspx?ImgID=Login',cookies=my_cookies)

    return request

def getLoginCatchImageCode(captch_request = None):
    open('img.png', 'wb').write(captch_request.content)

    ocr = ddddocr.DdddOcr(old=True)

    with open("img.png", 'rb') as f:
        image = f.read()

    res = ocr.classification(image)

    return res

def getCanLogintime(book_date):
    book_date_in_date_time = datetime.strptime(book_date, "%Y-%m-%d")
    
    start_book_date = book_date_in_date_time - timedelta(days=7)
    start_book_time = start_book_date.replace(hour=7,minute=59,second=30)
    tw_zone = pytz.timezone('Asia/Taipei')

    tw_start_login_time = tw_zone.localize(start_book_time)

    return tw_start_login_time

def getCanBooktime(book_date):
    book_date_in_date_time = datetime.strptime(book_date, "%Y-%m-%d")
    
    start_book_date = book_date_in_date_time - timedelta(days=7)
    start_book_time = start_book_date.replace(hour=8,minute=00,second=00)
    tw_zone = pytz.timezone('Asia/Taipei')

    tw_start_book_time = tw_zone.localize(start_book_time)

    return tw_start_book_time

def dateEncode(book_date):
    date = book_date.replace("-", "/")
    date = date + '5'
    date = '\x00'.join(date)

    message_bytes = date.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)

    string_bytes = str(base64_bytes, 'utf-8')
    
    return string_bytes 

def getTimeEnCode(time):
    mapping = {
        '08':' OAA1',
        '09':' OQA1',
        '10':'MQAwAA2',
        '11':'MQAxAA2',    
        '12':'MQAyAA2',
        '13':'MQAzAA2',
        '14':'MQA0AA2',
        '15':'MQA1AA2',
        '16':'MQA2AA2',
        '17':'MQA3AA2',
        '18':'MQA4AA2',
        '19':'MQA5AA2',
        '20':'MgAwAA2',
        '21':'MgAxAA2',
        '22':'MgAyAA2'
    }

    return mapping[time]

def getCookieCaptcha(web_driver):
    while True:
        cookies = web_driver.get_cookies()
        captch_request = captchImageResponse(cookies)
        captch_txt = getLoginCatchImageCode(captch_request)
        print(captch_txt)

        if len(captch_txt) == 4:
            break

    return captch_txt

def insertCaptcha(web_driver):
    print('insert Captcha start')
    captch_txt = getCookieCaptcha(web_driver)
   
    captcha_element = web_driver.find_element_by_id("ctl00_ContentPlaceHolder1_txtValidateCode")
    captcha_element.clear()
    captcha_element.send_keys(captch_txt)

def book(web_driver):
    print('book start')
    send_element = web_driver.find_element_by_id("ctl00_ContentPlaceHolder1_btnOrder")
    send_element.click()
   

if __name__ == '__main__':
    account = os.environ['ACCOUNT']
    password = os.environ['PASSWORD']
    book_date = os.environ['BOOK_DATE']

    start_time  = os.environ['START_BOOK_TIME']
    end_time  = os.environ['END_BOOK_TIME']
    place_number = os.environ.get('PLACE_NUMBER')

    can_login_time = getCanLogintime(book_date)
    can_book_time = getCanBooktime(book_date)

    try:
        web_driver = web_driver_init()

        pause.until(can_login_time)
        
        login(web_driver,account,password)
 
        date_code = dateEncode(book_date)
        if not place_number:
            place_number = 1
            
        parameter = {
            'date_code':date_code,
            'court_code':'MgA1',
            'start_time_code':getTimeEnCode(start_time),
            'end_time_code':getTimeEnCode(end_time),
            'place_number':place_number
        }

        readyBookPage(web_driver,parameter)
        
        pause.until(can_book_time)

        while True:
            book(web_driver)
            try:
                WebDriverWait(web_driver, 10).until(expected_conditions.alert_is_present())

                alert = web_driver.switch_to.alert
                text = alert.text
                print("after book alert text = {}".format(text))
                alert.accept()
               
    
                if text.find('驗證碼錯誤') > 0:
                    print(text.find('驗證碼錯誤'))
                    insertCaptcha(web_driver)
                    
                    continue
                # print(text.find('預約的場地數，已超過時段'))
                
                break
            except TimeoutException:
                print("no alert")
                
                break
    

    except Exception as e:
        print('out error message = {}'.format(e))
        web_driver.save_screenshot('error.png')
        
    web_driver.quit()