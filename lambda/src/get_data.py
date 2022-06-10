import datetime
from dateutil import tz
import json
import re
import requests
import time

session = requests.Session()
ID = ''
YEAR_MONTH = ''
JST = tz.gettz('Asia/Tokyo')


class YearMonth():
    year = 0
    month = 0
    year_month = ""

    def __init__(self, year_month):
        self.year_month = year_month.replace("-", "")
        self.year = int(year_month.split("-")[0])
        self.month = int(year_month.split("-")[1])

    def minus(self, minus):
        if minus <= 0:
            print("minus <= 0")
            return self.year_month
        if self.month > minus:
            self.month -= minus
        else:
            self.year -= 1
            self.month = 12 - (minus - self.month)
        self.year_month = str(self.year) + str(self.month).zfill(2)
        return self

    def get_year_month(self):
        return self.year_month

    def get_month(self):
        return self.month

    def get_year(self):
        return self.year


def init_requests(cookies):
    for cookie in cookies:
        session.cookies.set(cookie["name"], cookie["value"])
    ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36'
    headers = {'User-Agent': ua}
    session.headers = headers


def get_all(id, year_month, price):
    global ID
    ID = id
    # 前の月からのデータを取る
    year_month = YearMonth(year_month).minus(1)
    # アカウントチェック
    if not get_info():
        print("Can't access to account. ID: {}".format(ID))
        return None
    time.sleep(3)
    master_data = {}
    master_data = get_friends(master_data, year_month)
    time.sleep(3)
    master_data = get_genders(master_data, year_month)
    time.sleep(3)
    master_data = get_coupon(master_data, year_month, price)
    time.sleep(3)
    master_data = get_timeline(master_data, year_month)
    return master_data

def get_info():
    res = session.get(
        'https://manager.line.biz/api/bots/{0}/info'.format(ID),
        timeout=10
    )
    resDict = json.loads(res.text)
    if "activeStatus" in resDict and resDict["activeStatus"] == "ACTIVE":
        return True
    return False


def get_friends(master_data, year_month: YearMonth):
    data = []
    for i in range(6):
        monthly_data = {
                "year": year_month.get_year(),
                "month": year_month.get_month(),
                }

        res = session.get(
            'https://manager.line.biz/api/bots/{0}/insight/contacts'
            '?fromDate={1}01&toDate={1}31'.format(
                ID, year_month.get_year_month()),
            timeout=10
        )
        resDict = json.loads(res.text)
        if len(resDict["results"]) == 0:
            continue
        friends = resDict["results"][-1]["contacts"]
        monthly_data["total_number_of_friend"] = friends
        increased_friends = friends - resDict["summary"][
                "contacts"]["monthly"]["value"]
        monthly_data["total_number_of_friend_increased"] = increased_friends
        resDict = json.loads(res.text)
        data.append(monthly_data)
        if i == 0:
            num_of_blocks = resDict["results"][-1]["blocks"]
            master_data["number_of_block"] = num_of_blocks
        year_month = year_month.minus(1)
    master_data["friend"] = data
    return master_data

# You need 20 or more of relevant data to see this graph.なので、flaseで確認できません。
def get_genders(master_data, year_month: YearMonth):
    g_url = 'https://manager.line.biz/api/bots/{0}/insight/demographic'.format(ID)
    res = session.get(
        'https://manager.line.biz/api/bots/{0}/insight/demographic'.format(ID),
        timeout=10
    )
    resDict = json.loads(res.text)
    if resDict["available"] == "false":
        return master_data
    genders = resDict["genders"]
    ratio = {}
    for gender in genders:
        ratio[gender["gender"]] = gender["percentage"]
    ages = resDict["ages"]
    master_data["male_female_ratio"] = ratio
    age_group_of_friend = []
    for i, age in enumerate(ages):
        if i == 3:
            break
        data = {}
        data["ranking"] = i+1
        data["age_group"] = age["age"].replace("from", "").replace("to", "~")
        data["gender"] = age["gender"]
        data["percentage"] = age["percentage"]
        age_group_of_friend.append(data)
    master_data["age_group_of_friend"] = age_group_of_friend
    return master_data


def get_broadcasts(master_data, year_month: YearMonth):
    res = session.get(
        'https://manager.line.biz/api/bots/{0}/broadcasts'
        '?status=SENT&page=1&count=10'
        '&sort=SENT_DATE'.format(ID),
        timeout=10
    )
    resDict = json.loads(res.text)
    message_delivery = []
    query = ""
    for message in resDict["list"]:
        message_delivery.append({
            "id": message["id"],
            "number_of_delivery": message["deliveredCount"]
            })
        query += str(message["id"]) + ','

    res = session.get(
        'https://manager.line.biz/api/bots/{0}/insight/broadcastOverview'
        '?broadcastIds={1}'.format(ID, query),
        timeout=10
    )
    resDict = json.loads(res.text)
    broadcasts = resDict["broadcasts"]
    for i in range(len(message_delivery)):
        message = message_delivery[i]
        message_id = str(message["id"])
        timestamp = broadcasts[message_id][-1]["timestamp"]
        t = datetime.datetime.fromtimestamp(timestamp).astimezone(JST)
        message["delivery_date_time"] = t.strftime('%Y/%m/%d')
        number_of_click = broadcasts[message_id][-1]["uniqueClick"]
        number_of_open = broadcasts[message_id][-1]["uniqueImpression"]
        if number_of_click is None:
            message["number_of_click"] = 0
        else:
            message["number_of_click"] = number_of_click
        message["number_of_open"] = number_of_open
        del message["id"]
        message_delivery[i] = message
    master_data["message_delivery"] = message_delivery
    return master_data


def get_timeline(master_data, year_month: YearMonth):
    res = session.get(
        'https://manager.line.biz/api/bots/{0}/timeline/v2/postentry/list'
        '?postLimit=30'.format(ID),
        timeout=10
    )
    resDict = json.loads(res.text)
    posts = resDict["posts"]
    timeline = []
    for post in posts:
        data = {}
        timestamp = post["postInfo"]["createdTime"] / 1000
        t = datetime.datetime.fromtimestamp(timestamp).astimezone(JST)
        if int(t.strftime("%m")) != year_month.get_month():
            continue
        data["delivery_date_time"] = t.strftime('%Y/%m/%d')
        data["number_of_view"] = post["statistics"]["impressions"]
        data["number_of_like"] = post["statistics"]["likes"]
        data["number_of_comment"] = post["statistics"]["comments"]
        timeline.append(data)
    master_data["timeline"] = timeline
    return master_data


def get_coupon(master_data, year_month: YearMonth, price):
    res = session.get(
        'https://manager.line.biz/api/bots/{0}/coupons/list'
        '?title=&page=1&sortBy=&order=NONE'.format(ID),
        timeout=10
    )
    resDict = json.loads(res.text)
    coupons = resDict["list"]
    number_of_coupon_user = 0
    total_amount = 0
    for coupon in coupons:
        c_url = 'https://manager.line.biz/api/bots/{0}/insight/coupons/{1}'.format(ID, coupon["couponId"])
        res = session.get(
            'https://manager.line.biz/api/bots/{0}/insight/coupons/{1}'
            .format(ID, coupon["couponId"]),
            timeout=10
        )
        title = coupon["title"]
        discount = get_coupon_info(title)
        resDict = json.loads(res.text)
        if len(resDict["results"]) > 0:
            user = resDict["results"][0]["used"]
            number_of_coupon_user += user
            if discount is not None and "円" in discount:
                if int(discount.replace("円", "")) >= price:
                    print("Discount error: {}".format(discount))
                else:
                    total_amount += user * (
                        price - int(discount.replace("円", "")))
            elif discount is not None and '¥' in discount:
                if int(discount.replace("¥", "")) >= price:
                    print("Discount error: {}".format(discount))
                else:
                    total_amount += user * (
                            price - int(discount.replace("¥", "")))
            elif discount is not None and "%" in discount:
                if int(discount.replace("%", "")) >= 100:
                    print("Discount error: {}".format(discount))
                else:
                    total_amount += int(user * (
                        price * (1 - int(discount.replace("%", "")) / 100)))
    master_data["number_of_coupon_user"] = number_of_coupon_user
    master_data["sale"] = total_amount
    return master_data


def get_coupon_info(title):
    m = re.search(r'\d+円', title)
    if m is not None:
        r = m.group()
        return r
    m = re.search(r'\d+%', title)
    if m is not None:
        r = m.group()
        return r
    m = re.search(r'¥?\d+', title)
    if m is not None:
        r = m.group()
        return r

if __name__ == '__main__':


    # #
    file = open("./cookie.txt", "r")
    cookies = json.load(file)
    init_requests(cookies)
    year_month = YearMonth("2022-06")
    # # ID = "@770hqaux"
    ID = "@978cinfd"



    # print(json.dumps(get_genders({}, "2021-10")))
    # print(json.dumps(get_all(ID, "2021-10")))
    # print(get_friends({}, year_month))
    # print(get_genders({}, year_month))
    # print(get_broadcasts({}, year_month))
    print(get_timeline({}, year_month))
    # print(get_info())
    # print(get_coupon({}, year_month,1000))
    # get_broadcasts({}, year_month)
    # print(json.dumps(get_broadcasts({}, year_month)))
    # print(get_coupon({}, year_month, 1000))
