import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pymongo import MongoClient
from datetime import datetime, timedelta, time
import os
import pytz

# Environment variables or replace with your actual credentials
MONGO_URI = os.getenv('MONGO_URI')  # Replace with your MongoDB URI
GMAIL_USER = os.getenv('GMAIL_USER')  # Replace with your Gmail user
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')  # Replace with your Gmail password

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
        msg['To'] = 'abdulrahmanhany93@gmail.com'  # Replace with the recipient's email
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
                .summary, .today-summary, .month-summary {{
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

                <!-- Current Month's Summary -->
                <div class="month-summary">
                    <h3>Current Month's Report</h3>
                    <p>Total Orders This Month: <span class="highlight">{data['total_orders_month']}</span></p>
                    <p>Total Revenue This Month: <span class="highlight">{data['total_revenue_month']:.2f} L.E</span></p>
                    <p>Your Personal Revenue This Month: <span class="highlight">{data['personal_revenue_month']:.2f} L.E</span></p>
                    <p>Average Order Value This Month: <span class="highlight">{data['avg_order_value_month']:.2f} L.E</span></p>
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
    now = datetime.now(egypt_tz)

    # Calculate the start and end times for today's report
    if now.hour >= 11:
        today_start = now.replace(hour=11, minute=0, second=0, microsecond=0)
    else:
        today_start = (now - timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(hours=15, minutes=45)  # 2:45 AM next day

    # Calculate the start and end of the current month
    month_start = egypt_tz.localize(datetime(now.year, now.month, 1, 0, 0, 0))
    month_end = (month_start + timedelta(days=32)).replace(day=1, hour=23, minute=59, second=59, microsecond=999999) - timedelta(days=1)

    # Fetch data for full report
    total_restaurants = db['restaurants'].count_documents({'isActive': True})
    total_users = db['users'].count_documents({})
    total_new_users = db['users'].count_documents({'createdAt': {'$gte': today_start, '$lte': today_end}})

    # Variables for storing cumulative data
    total_orders = 0
    total_revenue = 0.0
    total_orders_today = 0
    total_revenue_today = 0.0
    total_orders_month = 0
    total_revenue_month = 0.0

    # Fetch orders for full report
    full_orders = db['orders'].find({
        'orderStatus': {'$nin': ['CANCELLED', 'PENDING']},
        'orderDate': {'$gte': start_date, '$lte': end_date}
    })

    # Fetch orders for today's report
    today_orders = db['orders'].find({
        'orderStatus': {'$nin': ['CANCELLED', 'PENDING']},
        'orderDate': {'$gte': today_start, '$lte': today_end}
    })

    # Fetch orders for current month's report
    month_orders = db['orders'].find({
        'orderStatus': {'$nin': ['CANCELLED', 'PENDING']},
        'orderDate': {'$gte': month_start, '$lte': month_end}
    })

    # Calculate totals for full report
    full_orders_list = list(full_orders)
    total_orders = len(full_orders_list)
    total_revenue = sum(order.get('orderAmount', 0) for order in full_orders_list)

    # Calculate totals for today's report
    today_orders_list = list(today_orders)
    total_orders_today = len(today_orders_list)
    total_revenue_today = sum(order.get('orderAmount', 0) for order in today_orders_list)

    # Calculate totals for current month's report
    month_orders_list = list(month_orders)
    total_orders_month = len(month_orders_list)
    total_revenue_month = sum(order.get('orderAmount', 0) for order in month_orders_list)

    # Calculate personal revenue (assuming 0.25% of 1% of total revenue)
    personal_revenue_full = total_revenue * 0.01 * 0.25
    personal_revenue_today = total_revenue_today * 0.01 * 0.25
    personal_revenue_month = total_revenue_month * 0.01 * 0.25

    # Calculate average order value
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    avg_order_value_today = total_revenue_today / total_orders_today if total_orders_today > 0 else 0
    avg_order_value_month = total_revenue_month / total_orders_month if total_orders_month > 0 else 0

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
        'avg_order_value_today': avg_order_value_today,
        'total_orders_month': total_orders_month,
        'total_revenue_month': total_revenue_month,
        'personal_revenue_month': personal_revenue_month,
        'avg_order_value_month': avg_order_value_month
    }

# Function to run the report generation and sending process
def run_report(start_date_str):
    # Parse the start date string for the full report
    start_date = datetime.strptime(start_date_str, "%d-%m-%Y")
    start_date = egypt_tz.localize(start_date.replace(hour=0, minute=0, second=0, microsecond=0))

    # Set the end_date to now
    now = datetime.now(egypt_tz)
    end_date = now

    # Fetch the report data for the specified range
    data = fetch_report_data(start_date, end_date)
    html_report = generate_html_report(data)
    send_report_email(html_report)

if __name__ == "__main__":
    start_date_str = "26-09-2024"  # Replace with the desired start date
    run_report(start_date_str)
