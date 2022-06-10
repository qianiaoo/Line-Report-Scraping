import os
import pymysql


def get_companies():
    print("=========Get companies=========")
    companies = []
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            passwd=os.getenv("DB_PASSWORD"),
            db='line_report',
            connect_timeout=5
            )
        cur = conn.cursor()
        cur.execute("SELECT line_id, name, email, email_password, price "
                    "FROM lineReport_company "
                    "WHERE is_active = 1 and is_superuser = 0 AND is_staff = 0"
                    )
        rows = cur.fetchall()
        for row in rows:
            company = {}
            company["line_id"] = row[0]
            company["name"] = row[1]
            company["email"] = row[2]
            company["email_password"] = row[3]
            company["price"] = row[4]
            companies.append(company)
        cur.close()
        conn.close()
    except Exception as e:
        print(e)

    print(companies)
    return companies
