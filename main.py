from email.mime.text import MIMEText

import requests
from twilio.rest import Client
from smtplib import SMTP
import os
from dotenv import load_dotenv
load_dotenv()

STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"

STOCK_API_KEY = os.getenv("STOCK_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

ACCOUNT_SID = os.getenv("TWILIO_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
MY_PHONE = os.getenv("MY_PHONE")

MY_EMAIL = os.getenv("MY_EMAIL")
MY_PASSWORD = os.getenv("MY_PASSWORD")

stock_parameters = {
    "function": "TIME_SERIES_DAILY",
    "symbol":STOCK,
    "apikey": STOCK_API_KEY,
}

response = requests.get("https://www.alphavantage.co/query", params=stock_parameters)
response.raise_for_status()
data = response.json()

if "Time Series (Daily)" not in data:
    print(data)
    exit()

stock_data = data["Time Series (Daily)"]

# Get date in descending order
date = sorted(stock_data.keys(), reverse=True)

day_before_yesterday = date[1]
yesterday = date[0]
day_before_yesterday_close = float(stock_data[day_before_yesterday]["4. close"])
yesterday_close = float(stock_data[yesterday]["4. close"])

# Calculate price movements
price_difference = yesterday_close - day_before_yesterday_close

percentage_change = (price_difference / day_before_yesterday_close ) * 100

if abs(percentage_change) > 1:

    news_parameters = {
        "apiKey": NEWS_API_KEY,
        "qInTitle": COMPANY_NAME,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 3
    }

    news_response = requests.get("https://newsapi.org/v2/everything", params=news_parameters)
    news_response.raise_for_status()
    news_data = news_response.json().get("articles", [])

    direction= "🔺" if percentage_change > 0 else "🔻"
    message_body = f"{STOCK}: {direction}{abs(percentage_change):.2f}%\n\n"

    with SMTP("smtp.gmail.com", port=587) as connection:

        for article in news_data:
            title = article.get("title", "No title")
            description = article.get("description", "No description")
            message_body += (
                f"Headline: {title}\n"
                f"Brief: {description}"
            )

        message_body = message_body[:1500]

        connection.starttls()
        connection.login(user=MY_EMAIL, password=MY_PASSWORD)

        # Send message through Gmail
        msg = MIMEText(message_body, "plain", "utf-8")
        msg["subject"] = "STOCK UPDATE"
        msg["from"] = MY_EMAIL
        msg["to"] = MY_EMAIL

        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=MY_EMAIL,
            msg=msg.as_string()
        )

        # Send message from Twilio Number to my Number
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE,
            to=MY_PHONE
        )

        print("Message sent:", message.status)
else:
    print("No significant change. No news sent.")

