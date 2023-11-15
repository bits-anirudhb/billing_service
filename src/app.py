from flask import Flask, render_template, request, redirect, url_for, session
import pymysql

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'

# Database Configuration (MySQL)
# Replace 'your_db_config' with your actual MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'billing_service_db'


def get_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True  # Added autocommit
    )


# Function to get user information from the user service
def get_user_info(user_id):
    # Replace the following with your actual logic to fetch user information
    # from the user service using user_id
    # For demonstration purposes, a placeholder dictionary is used.
    return {'username': 'admin'} if user_id == 1 else None


# Initialize the tables and juice menu
def initialize_database():
    with get_connection() as connection, connection.cursor() as cursor:
        # Create tables
        cursor.execute("CREATE TABLE IF NOT EXISTS tables (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(50) NOT NULL UNIQUE)")
        cursor.execute("INSERT IGNORE INTO tables (name) VALUES ('Table 1'), ('Table 2'), ('Table 3'), ('Table 4'), ('Table 5')")

        # Create juice menu
        cursor.execute("CREATE TABLE IF NOT EXISTS juice_menu (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(50) NOT NULL UNIQUE, price DECIMAL(5, 2) NOT NULL)")
        cursor.execute(
            "INSERT IGNORE INTO juice_menu (name, price) VALUES ('Orange Juice', 2.50), ('Apple Juice', 3.00), ('Carrot Juice', 2.75), ('Strawberry Juice', 3.50), ('Mango Juice', 4.00)")

        # Create orders and order_items tables
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS orders (order_id INT PRIMARY KEY AUTO_INCREMENT, table_id INT, order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id INT PRIMARY KEY AUTO_INCREMENT,
                order_id INT,
                juice_id INT,
                quantity INT,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        """)


initialize_database()


# Main route - Display the billing page
@app.route('/')
def billing():
    try:
        # Fetch tables for the dropdown
        with get_connection() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tables")
            tables = cursor.fetchall()

        # Get user information from the user service
        user_id = session.get('user_id')
        user_info = get_user_info(user_id)

        # Pass the welcome message to the template
        welcome_message = f"Welcome, {user_info['username']}!" if user_info else "Welcome, Guest!"
        return render_template('billing.html', welcome_message=welcome_message, tables=tables)
    except Exception as e:
        print(f"Error in billing route: {e}")
        return "An error occurred while processing your request."


# Route for processing the selected table and displaying juice menu
@app.route('/process_table', methods=['POST'])
def process_table():
    try:
        table_id = request.form.get('table_id')

        # Fetch juice menu based on the selected table
        with get_connection() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM juice_menu")
            juice_menu = cursor.fetchall()

        return render_template('order.html', selected_table=table_id, juice_menu=juice_menu)
    except Exception as e:
        print(f"Error in process_table route: {e}")
        return "An error occurred while processing your request."


# Route for processing the selected juices and quantities
@app.route('/process_order', methods=['POST'])
def process_order():
    try:
        table_id = request.form.get('table_id')
        selected_juices = []

        # Extract selected juices and quantities
        for juice_id in request.form.getlist('juices'):
            quantity = request.form.get(f'quantity_{juice_id}', type=int, default=0)

            if quantity > 0:
                selected_juices.append({'id': juice_id, 'quantity': quantity})

        # Debug: Print received data
        print(f"Table ID: {table_id}")
        print("Selected Juices:", selected_juices)

        # Store the order in the database
        with get_connection() as connection, connection.cursor() as cursor:
            # Create an order record
            cursor.execute("INSERT INTO orders (table_id) VALUES (%s)", (table_id,))
            order_id = cursor.lastrowid
           # Retrieve the order_id
            cursor.execute("SELECT LAST_INSERT_ID()")
            order_id = cursor.fetchone()['LAST_INSERT_ID()']

            # Insert order details into order_items table
            for juice in selected_juices:
                cursor.execute(
                    "INSERT INTO order_items (order_id, juice_id, quantity) VALUES (%s, %s, %s)",
                    (order_id, juice['id'], juice['quantity'])
                )

            # Commit the transaction
            connection.commit()

            # Fetch and print order_items for debugging
            cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
            order_items = cursor.fetchall()
            print(f"DEBUG: order_items for Order ID {order_id} - {order_items}")
        return render_template('success.html', table_id=table_id, selected_juices=selected_juices)
    except Exception as e:
        print(f"Error in process_order route: {e}")
        return "An error occurred while processing your request."


if __name__ == '__main__':
    app.run(debug=True, port=5001)
