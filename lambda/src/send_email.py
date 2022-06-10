from boto3.session import Session
from cryptography.fernet import Fernet
import os

FROM_ADDRESS = os.getenv("FROM_ADDRESS")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")


def get_session():
    if os.getenv('ENV') == 'DEV':
        session = Session(
            profile_name='line-lambda',
            region_name='ap-northeast-1',
        )
    else:
        session = Session(region_name='ap-northeast-1')
    return session


def send(client, title, body, to_address):
    print("=========SEND EMAIL=========")
    client.send_email(
        Source=FROM_ADDRESS,
        Destination={
            'ToAddresses': [to_address]
        },
        Message={
            'Subject': {
                'Data': title,
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': body,
                    'Charset': 'UTF-8'
                }
            }
        },
        ReplyToAddresses=[FROM_ADDRESS]
    )


def create_email_body(name, line_id, email_password):
    return \
        "{}御中\n\n" \
        "いつもお世話になっております。\nLINE BOMB運営本部です。\n\n" \
        "先月の分析レポートを送付させていただきますので、ご確認ください。\n\n" \
        "URL：https://line-report.link/\n" \
        "LINE ID：{}\n" \
        "パスワード：{}\n" \
        "上記URLよりアクセスしていただき、LINE IDとパスワードをご入力ください。\n\n" \
        "引き続きどうぞよろしくお願い申し上げます。\n".format(name, line_id, email_password)


def send_email(company):
    name = company["name"]
    line_id = company["line_id"]
    email = company["email"]
    email_password = company["email_password"]
    session = get_session()
    ses_client = session.client('ses')
    title = "LINE 分析レポートのお知らせ"

    f = Fernet(ENCRYPTION_KEY)
    try:
        decrypt_email_password = f.decrypt(email_password.encode()).decode()
        send(ses_client, title, create_email_body(
            name, line_id, decrypt_email_password), email
        )
        print("EMAIL SENT")
    except Exception:
        print("PASSWORD DECRYPT FAILED")
