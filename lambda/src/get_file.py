from boto3.session import Session
import os

BUCKET_NAME = 'arts-line-report'
END_POINT = 's3://arts-line-report'


def get_s3(file_name):
    print("=========Get cokkie=========")
    if os.getenv('ENV') == 'DEV':
        session = Session(
            profile_name='line-lambda',
        )
    else:
        session = Session()
    s3 = session.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)
    obj = bucket.Object(file_name).get()
    return obj['Body'].read().decode()


if __name__ == '__main__':
    get_s3('test.txt')
