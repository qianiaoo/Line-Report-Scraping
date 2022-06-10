# coding:utf-8
from boto3.session import Session
import json
import os
from selenium import webdriver
import sys
from time import sleep

BUCKET_NAME = 'arts-line-report'
FILE_NAME = 'cookie.txt'
END_POINT = 's3://arts-line-report'

if len(sys.argv) >= 2 and sys.argv[1] == "email":
    FILE_NAME = "cookie-email.txt"

try:
    # ブラウザを開く。
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-logging')
    driver = webdriver.Chrome(
            executable_path="./chromedriver", chrome_options=options)

    driver.get('https://account.line.biz/login?'
               'redirectUri=https%3A%2F%2Fmanager.line.biz%2F')

    element = driver.find_element_by_class_name("btn-primary")
    element.click()
    driver.get(driver.current_url.replace("#/", "#/qr"))
    url = driver.current_url

    # ログイン待ち
    while url != 'https://manager.line.biz/':
        sleep(2)
        url = driver.current_url

    # Cookieをファイルに保存
    file = open(FILE_NAME, "w")
    file.write(json.dumps(driver.get_cookies()))
    file.close()

    # # AWSのS3にCookie情報をアップロードする
    # session = Session(profile_name='s3admin')
    # # session = Session()
    # s3 = session.resource('s3')
    # bucket = s3.Bucket(BUCKET_NAME)
    # bucket.upload_file(FILE_NAME, FILE_NAME)
    #
    # # Cookieのファイルは削除する
    # os.remove(FILE_NAME)

finally:
    # ブラウザを終了する。
    driver.quit()
