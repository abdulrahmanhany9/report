import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pymongo import MongoClient
from datetime import datetime, timedelta, time
import os
import pytz

MONGO_URI = os.getenv('MONGO_URI')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
egypt_tz = pytz.timezone('Africa/Cairo')
current_time = datetime.now(egypt_tz).time()

# Define the start and end times
start_time = time(11, 0)  # 11:00 AM
end_time = time(3, 0)     # 3:00 AM (next day)

# Check if the current time is within the allowed range
if not ((start_time <= current_time) or (current_time <= end_time)):
    print("Script is running outside the allowed time range (11:00 AM to 3:00 AM). Exiting.")
    exit()

# MongoDB connection settings
client = MongoClient(MONGO_URI)
db = client['alaadev']

# Function to send an email
def send_report_email(html_content):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_USER
        msg['To'] = 'abdulrahmanhany93@gmail.com'
        msg['Subject'] = "Business Performance Report"

        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)

        server.sendmail(GMAIL_USER, 'abdulrahmanhany93@gmail.com', msg.as_string())
        server.quit()

        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Function to generate the styled HTML content
def generate_html_report(data):
    html_content = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    color: #333;
                    padding: 20px;
                }}
                .container {{
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    max-width: 800px;
                    margin: auto;
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #e4e4e4;
                }}
                .title {{
                    font-size: 28px;
                    color: #007bff;
                }}
                .summary, .today-summary {{
                    margin-top: 20px;
                    font-size: 16px;
                    line-height: 1.5;
                }}
                .highlight {{
                    color: #007bff;
                    font-weight: bold;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                    margin-top: 20px;
                    border-top: 1px solid #e4e4e4;
                    padding-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 class="title">Business Performance Report</h2>
                </div>

                <!-- Full Summary -->
                <div class="summary">
                    <h3>Full Report (From Start to Now)</h3>
                    <p>Total Active Restaurants: <span class="highlight">{data['total_restaurants']}</span></p>
                    <p>Total Users: <span class="highlight">{data['total_users']}</span></p>
                    <p>Total Orders: <span class="highlight">{data['total_orders']}</span></p>
                    <p>Total Revenue: <span class="highlight">{data['total_revenue']:.2f} L.E</span></p>
                    <p>Your Total Personal Revenue: <span class="highlight">{data['personal_revenue_full']:.2f} L.E</span></p>
                    <p>Average Order Value: <span class="highlight">{data['avg_order_value']:.2f} L.E</span></p>
                </div>

                <!-- Today's Summary -->
                <div class="today-summary">
                    <h3>Today's Report (11:00 AM to 2:45 AM)</h3>
                    <p>New Users Today: <span class="highlight">{data['total_new_users']}</span></p>
                    <p>Total Orders Today: <span class="highlight">{data['total_orders_today']}</span></p>
                    <p>Total Revenue Today: <span class="highlight">{data['total_revenue_today']:.2f} L.E</span></p>
                    <p>Your Personal Revenue Today: <span class="highlight">{data['personal_revenue_today']:.2f} L.E</span></p>
                    <p>Average Order Value Today: <span class="highlight">{data['avg_order_value_today']:.2f} L.E</span></p>
                </div>

                <div class="footer">
                    <p>Generated on: {datetime.now(egypt_tz).strftime('%d-%m-%Y %H:%M')}</p>
                </div>
            </div>
        </body>
    </html>
    """
    return html_content

# Function to fetch and process data
def fetch_report_data(start_date, end_date):
    # Calculate the start and end times for today's report
    now = datetime.now(egypt_tz)
    if now.hour >= 11:
        today_start = now.replace(hour=11, minute=0, second=0, microsecond=0)
        today_end = (today_start + timedelta(days=1)).replace(hour=2, minute=45, second=59, microsecond=999999)
    else:
        # Before 11 AM, the reporting period is still part of the previous day
        today_start = (now - timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(hours=15, minutes=45)

    # Fetch full report data from the specified start_date to the end_date
    total_restaurants = db['restaurants'].count_documents({'isActive': True})
    total_users = db['users'].count_documents({})
    total_new_users = db['users'].count_documents({'createdAt': {'$gte': today_start, '$lte': today_end}})

    total_orders = 0
    total_orders_today = 0
    total_revenue = 0
    total_revenue_today = 0

    # Iterate over restaurants for both full and today's data
    restaurants = db['restaurants'].find({'isActive': True})
    for restaurant in restaurants:
        restaurant_id = restaurant['_id']

        # Full report data (from start_date to end_date)
        orders = list(db['orders'].find({
    'restaurant': restaurant_id,
    'orderStatus': {'$nin': ['CANCELLED', 'PENDING']},
    'orderDate': {'$gte': start_date, '$lte': end_date}
}))
        restaurant_total_orders = len(orders)
        restaurant_total_revenue = sum(order['orderAmount'] for order in orders if 'orderAmount' in order)

        # Today's report data (from today_start to today_end)
        today_orders = list(db['orders'].find({
            'restaurant': restaurant_id,
            'orderStatus': {'$ne': 'CANCELLED'},
            'orderDate': {'$gte': today_start, '$lte': today_end}
        }))
        restaurant_total_orders_today = len(today_orders)
        restaurant_total_revenue_today = sum(order['orderAmount'] for order in today_orders if 'orderAmount' in order)

        total_orders += restaurant_total_orders
        total_orders_today += restaurant_total_orders_today
        total_revenue += restaurant_total_revenue
        total_revenue_today += restaurant_total_revenue_today

    # Calculate personal revenue for full report and today's report
    personal_revenue_full = total_revenue * 0.01 * 0.25
    personal_revenue_today = total_revenue_today * 0.01 * 0.25

    # Average order values
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    avg_order_value_today = total_revenue_today / total_orders_today if total_orders_today > 0 else 0

    return {
        'total_restaurants': total_restaurants,
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'personal_revenue_full': personal_revenue_full,
        'total_new_users': total_new_users,
        'total_orders_today': total_orders_today,
        'total_revenue_today': total_revenue_today,
        'personal_revenue_today': personal_revenue_today,
        'avg_order_value': avg_order_value,
        'avg_order_value_today': avg_order_value_today
    }

# Function to run the report generation and sending process
def run_report(start_date_str):
    # Parse the start date string
    start_date = datetime.strptime(start_date_str, "%d-%m-%Y")
    start_date = egypt_tz.localize(start_date.replace(hour=11, minute=0, second=0, microsecond=0))

    # Set the end_date to now's period boundary (2:45 AM of the next day)
    now = datetime.now(egypt_tz)
    if now.hour < 5:
        end_date = now.replace(hour=2, minute=45, second=59, microsecond=999999)
    else:
        end_date = (now + timedelta(days=1)).replace(hour=2, minute=45, second=59, microsecond=999999)

    # Fetch the report data for the specified range
    data = fetch_report_data(start_date, end_date)
    html_report = generate_html_report(data)
    send_report_email(html_report)

if __name__ == "__main__":
    start_date_str = "26-09-2024"
    run_report(start_date_str)