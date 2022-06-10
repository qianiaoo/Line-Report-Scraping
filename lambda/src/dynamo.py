from boto3.session import Session
from botocore.exceptions import ClientError
import os

TABLE_NAME = 'line-customer-data'
REGION = 'ap-northeast-1'


def get_dynamo_table():
    if os.getenv('ENV') == 'DEV':
        session = Session(
            profile_name='line-lambda',
            region_name=REGION,
        )
    else:
        session = Session(region_name=REGION)
    dynamodb = session.resource('dynamodb')
    dynamo_table = dynamodb.Table(TABLE_NAME)
    return dynamo_table

# handle a year_month string to be last_year_month
def last_year_month(year_month):
    year = int(year_month.split("-")[0])
    month = int(year_month.split("-")[1])
    if month > 1:
        month -= 1
    else:
        year -= 1
        month = 12
    return "{0}-{1}".format(year, month)


def put_data(id, year_month, data):
    print("=========Add data to dynamo=========")
    table = get_dynamo_table()
    response = table.put_item(
        Item={
            'id': id,
            'year_month': last_year_month(year_month),
            'data': data,
        }
    )
    return response


def get_data(id, year_month):
    table = get_dynamo_table()
    try:
        response = table.get_item(Key={
            'id': id,
            'year_month': last_year_month(year_month)
        })
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        if "Item" in response:
            return response["Item"]
    return None


if __name__ == '__main__':
    # data = sample_data.data
    # res = put_data('test', '2021-12', data)
    # print('succeeded')
    # pprint(res)
    print(get_data('@978cinfd', '2021-12'))
