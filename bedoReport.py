import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pymongo import MongoClient
from datetime import datetime, timedelta

# MongoDB connection settings
MONGO_URI = "mongodb+srv://api-application:9RMeQ08hTGRFtL2i@cluster0.jcitrgd.mongodb.net/alaadev?retryWrites=true&w=majority"  # Add your MongoDB URI here
client = MongoClient(MONGO_URI)
db = client['alaadev']

# Gmail credentials
GMAIL_USER = 'bedojobs@gmail.com'
GMAIL_PASSWORD = 'bvkf indh uthn toel'

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
                .summary {{
                    margin-top: 20px;
                    font-size: 16px;
                    line-height: 1.5;
                }}
                .highlight {{
                    color: #007bff;
                    font-weight: bold;
                }}
                .restaurant-details {{
                    margin-top: 20px;
                }}
                .restaurant {{
                    background-color: #f9f9f9;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    margin-bottom: 10px;
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
                <div class="summary">
                    <p>Total Active Restaurants: <span class="highlight">{data['total_restaurants']}</span></p>
                    <p>Total Orders : <span class="highlight">{data['total_orders']}</span></p>
                    <p>Total Orders (Today): <span class="highlight">{data['total_orders_today']}</span></p>
                    <p>Total Revenue : <span class="highlight">{data['total_revenue']:.2f} L.E</span></p>
                    <p>Total Revenue (Today): <span class="highlight">{data['total_revenue_today']:.2f} L.E</span></p>
                    <p>Average Order Value : <span class="highlight">{data['avg_order_value']:.2f} L.E</span></p>
                    <p>Average Order Value (Today): <span class="highlight">{data['avg_order_value_today']:.2f} L.E</span></p>
                    <p>Order Growth: <span class="highlight">{data['order_growth']:.2f}%</span></p>
                    <p>Top Performing Restaurant : <span class="highlight">{data['top_restaurant']}</span></p>
                    <p>Top Performing Restaurant (Today): <span class="highlight">{data['top_restaurant_today']}</span></p>
                    <p>Your Total Revenue : <span class="highlight">{data['additional_calc_period']:.2f} L.E</span></p>
                    <p>Your Total Revenue (Today): <span class="highlight">{data['additional_calc_today']:.2f} L.E</span></p>
                    <p>Total Users: <span class="highlight">{data['total_users']}</span></p>
                    <p>New Users : <span class="highlight">{data['total_new_users']}</span></p>
                    <p>New Users (Today): <span class="highlight">{data['total_new_users_today']}</span></p>
                </div>
                <div class="restaurant-details">
                    <h3>Restaurant Details:</h3>
                    {data['restaurant_details']}
                </div>
                <div class="footer">
                    <p>Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M')}</p>
                </div>
            </div>
        </body>
    </html>
    """
    return html_content

# Function to fetch and process data
def fetch_report_data(start_date, end_date):
    start_date = start_date.replace(hour=11, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=2, minute=45, second=59, microsecond=999999)

    today_start = datetime.now().replace(hour=11, minute=0, second=0, microsecond=0)
    today_end = (today_start + timedelta(days=1)).replace(hour=2, minute=45, second=59, microsecond=999999)

    previous_period_start = start_date - (end_date - start_date)

    total_restaurants = db['restaurants'].count_documents({'isActive': True})
    total_users = db['users'].count_documents({})
    total_new_users = db['users'].count_documents({'createdAt': {'$gte': start_date, '$lte': end_date}})
    total_new_users_today = db['users'].count_documents({'createdAt': {'$gte': today_start, '$lte': today_end}})

    total_orders = 0
    total_orders_today = 0
    total_revenue = 0
    total_revenue_today = 0
    restaurant_details = ""
    restaurant_revenues = {}
    restaurant_revenues_today = {}

    restaurants = db['restaurants'].find({'isActive': True})
    for restaurant in restaurants:
        restaurant_id = restaurant['_id']
        restaurant_name = restaurant['name']

        orders = list(db['orders'].find({
            'restaurant': restaurant_id,
            'orderStatus': {'$ne': 'CANCELLED'},
            'orderDate': {'$gte': start_date, '$lte': end_date}
        }))
        restaurant_total_orders = len(orders)
        restaurant_total_revenue = sum(order['orderAmount'] for order in orders if 'orderAmount' in order)

        today_orders = list(db['orders'].find({
            'restaurant': restaurant_id,
            'orderStatus': {'$ne': 'CANCELLED'},
            'orderDate': {'$gte': today_start, '$lte': today_end}
        }))
        restaurant_total_orders_today = len(today_orders)
        restaurant_total_revenue_today = sum(order['orderAmount'] for order in today_orders if 'orderAmount' in order)

        restaurant_revenues[restaurant_name] = restaurant_total_revenue
        restaurant_revenues_today[restaurant_name] = restaurant_total_revenue_today

        total_orders += restaurant_total_orders
        total_orders_today += restaurant_total_orders_today
        total_revenue += restaurant_total_revenue
        total_revenue_today += restaurant_total_revenue_today

        restaurant_details += f"""
        <div class="restaurant">
            <p>Restaurant: <span class="highlight">{restaurant_name}</span></p>
            <p>Total Orders : <span class="highlight">{restaurant_total_orders}</span></p>
            <p>Total Orders (Today): <span class="highlight">{restaurant_total_orders_today}</span></p>
            <p>Total Revenue : <span class="highlight">{restaurant_total_revenue:.2f} L.E</span></p>
            <p>Total Revenue (Today): <span class="highlight">{restaurant_total_revenue_today:.2f} L.E</span></p>
        </div>
        """

    additional_calc_period = (total_revenue * 0.01) / 4
    additional_calc_today = (total_revenue_today * 0.01) / 4

    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    avg_order_value_today = total_revenue_today / total_orders_today if total_orders_today > 0 else 0

    previous_orders = db['orders'].count_documents({'orderDate': {'$gte': previous_period_start, '$lte': start_date}})
    order_growth = ((total_orders - previous_orders) / previous_orders) * 100 if previous_orders > 0 else 0

    top_restaurant = max(restaurant_revenues, key=restaurant_revenues.get) if restaurant_revenues else "N/A"
    top_restaurant_today = max(restaurant_revenues_today, key=restaurant_revenues_today.get) if restaurant_revenues_today else "N/A"

    return {
        'total_restaurants': total_restaurants,
        'total_orders': total_orders,
        'total_orders_today': total_orders_today,
        'total_revenue': total_revenue,
        'total_revenue_today': total_revenue_today,
        'avg_order_value': avg_order_value,
        'avg_order_value_today': avg_order_value_today,
        'order_growth': order_growth,
        'top_restaurant': top_restaurant,
        'top_restaurant_today': top_restaurant_today,
        'additional_calc_period': additional_calc_period,
        'additional_calc_today': additional_calc_today,
        'total_users': total_users,
        'total_new_users': total_new_users,
        'total_new_users_today': total_new_users_today,
        'restaurant_details': restaurant_details
    }

# Function to run the report generation and sending process
def run_report():
    start_date = datetime.strptime("2024-09-26", "%Y-%m-%d")
    end_date = datetime.now()

    data = fetch_report_data(start_date, end_date)
    html_report = generate_html_report(data)
    send_report_email(html_report)

# Execute report generation
run_report()
