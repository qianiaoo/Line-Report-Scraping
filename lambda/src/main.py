import datetime
from dateutil import tz
import get_company
import get_data
import get_file
import dynamo
import json
import urllib
import send_email


def get_year_month():
    JST = tz.gettz('Asia/Tokyo')
    t = datetime.datetime.now(JST)
    year_month = t.strftime('%Y-%m')
    return year_month


def get_filename(event):
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'],
        encoding='utf-8'
    )
    return key


def lambda_handler(event, context):
    print("=========START=========")
    print("=========CHECK MODE=========")
    MODE = "DATA"
    filename = get_filename(event)
    if filename == "cookie-email.txt":
        MODE = "EMAIL"
    print("MODE = {}".format(MODE))
    companies = get_company.get_companies()
    year_month = get_year_month()
    cookies_str = get_file.get_s3(filename)
    cookies = json.loads(cookies_str)
    get_data.init_requests(cookies)

    print("=========Fetching=========")
    for company in companies:
        line_id = company["line_id"]
        price = company["price"]
        print("LINE ID: {}".format(line_id))
        data = dynamo.get_data(line_id, year_month)
        if data is None:
            data = get_data.get_all(line_id, year_month, price)
            if data is not None:
                res = dynamo.put_data(line_id, year_month, data)
                if "HTTPStatusCode" in res and res["HTTPStatusCode"] == "200":
                    print("SUCCESS")
                else:
                    print("FAILED")
        else:
            print("SKIP FETCHING")
        if MODE == "EMAIL" and data is not None:
            send_email.send_email(company)
        else:
            print("SKIP EMAIL SENDING")

        print("==========NEXT==========")

    print("==========END==========")


def main():
    file = open("./event.json", "r")
    event = json.load(file)
    lambda_handler(event, None)


if __name__ == "__main__":
    main()
