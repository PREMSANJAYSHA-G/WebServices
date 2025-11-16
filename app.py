from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import pymysql
from pymysql import IntegrityError
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY"  # Required for session management
app.config.from_object(Config)

# ---- Flask-Mail Config ---------------------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'sanjaysha1803@gmail.com'      # Your Gmail
app.config['MAIL_PASSWORD'] = 'lgxl zapt daaq cwnv'           # Gmail App Password
mail = Mail(app)

# ------------------ DATABASE CONNECTION ------------------
def get_db():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor
    )

# ------------------ HOME ------------------
@app.route('/')
def home():
    return render_template("home.html")

# ------------------ SIGNUP ------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (name, email, hashed_password)
            )
            conn.commit()
            # Store session data
            session['username'] = name
            session['email'] = email
            flash("Signup successful! Welcome to your dashboard.", "success")
            return redirect(url_for('services'))

        except IntegrityError:
            flash("Email already exists. Try a different email.", "danger")
            return redirect(url_for('signup'))

        finally:
            cur.close()
            conn.close()

    return render_template('signup.html')

# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['name']
            session['email'] = user['email']  # Store email in session
            flash("Login successful!", "success")
            return redirect(url_for('services'))
        else:
            flash("Incorrect email or password!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# ------------------ LOGOUT ------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))

# ------------------ SERVICES ------------------
@app.route('/services')
def services():
    if 'username' not in session:
        flash("Please login to access services.", "warning")
        return redirect(url_for('login'))

    services_list = [
        {"id": 1, "name": "Creating Web Application", "price": "₹50,000", "details": "Full stack web application with backend and frontend."},
        {"id": 2, "name": "Cloud Deployment", "price": "₹20,000", "details": "Deploy your web app or services on cloud servers."},
        {"id": 3, "name": "Create App", "price": "₹60,000", "details": "Native or hybrid mobile app for iOS and Android."},
        {"id": 4, "name": "Digital Marketing", "price": "₹15,000", "details": "SEO, Social Media Marketing, and Ads campaigns."},
    ]

    return render_template("services.html", username=session['username'], services=services_list)

# ------------------ QUOTATION ------------------
@app.route('/quotation/<int:service_id>', methods=['GET', 'POST'])
def quotation(service_id):
    if 'username' not in session:
        flash("Please login first to request a quotation.", "warning")
        return redirect(url_for('login'))

    services_dict = {
        1: {"name": "Creating Web Application", "price": 50000, "details": "Full-stack web applications with backend, frontend, database integration."},
        2: {"name": "Cloud Deployment", "price": 20000, "details": "Deploy apps on AWS, Azure, GCP with full setup."},
        3: {"name": "Create App", "price": 60000, "details": "Native or hybrid mobile apps for iOS and Android."},
        4: {"name": "Digital Marketing", "price": 15000, "details": "SEO, Social Media Marketing, Google Ads campaigns."}
    }

    service = services_dict.get(service_id)
    if not service:
        flash("Service not found!", "danger")
        return redirect(url_for('services'))

    cgst = service['price'] * 0.05
    sgst = service['price'] * 0.05
    total = service['price'] + cgst + sgst

    if request.method == "POST":
        customer_name = session.get('username')
        customer_email = session.get('email')  # safer access
        message_text = request.form['message']

        # Send email notification
        msg = Message(
            subject=f"Quotation Request from {customer_name}",
            sender=customer_email,
            recipients=["sanjaysha1803@gmail.com"],
            body=f"""
User Name: {customer_name}
User Email: {customer_email}
Service: {service['name']}
Message/Requirements: {message_text}
Price: ₹{service['price']}
CGST (5%): ₹{cgst}
SGST (5%): ₹{sgst}
Total: ₹{total}
"""
        )
        mail.send(msg)

        flash(f"Quotation request for '{service['name']}' sent successfully!", "success")
        return redirect(url_for('services'))

    return render_template("quotation.html", service=service, cgst=cgst, sgst=sgst, total=total)

# ------------------ RUN APP ------------------
if __name__ == "__main__":
    app.run(debug=True)
