from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = 'SecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yourdatabase.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(1024), nullable=False)
    short_token = db.Column(db.String(80), unique=True, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)

serializer = URLSafeTimedSerializer(app.secret_key)

@app.route('/')
def home():
    # If the user is logged in, redirect to shorten link page
    if 'username' in session:
        return redirect(url_for('shorten_link_page'))
    # Otherwise, show home with login and signup options
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = user.username
            return redirect(url_for('home'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/l/<short_token>')
def redirect_to_original(short_token):
    try:
        original_url = serializer.loads(short_token, salt='short_link_salt', max_age=3600 * 48)
        link = Link.query.filter_by(short_token=short_token).first()
        if link and link.expiration_date > datetime.now():
            return redirect(original_url)
    except:
        return 'This link has expired or is invalid.'
    
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        session['username'] = new_user.username
        return redirect(url_for('home'))

    return render_template('signup.html')


@app.route('/shorten', methods=['GET', 'POST'])
def shorten_link_page():
    if 'username' in session:
        if request.method == 'POST':
            original_url = request.form['url']
            short_token = serializer.dumps(original_url, salt='short_link_salt')
            new_link = Link(original_url=original_url, short_token=short_token,
                            expiration_date=datetime.now() + timedelta(hours=48))
            db.session.add(new_link)
            db.session.commit()
            return redirect(url_for('view_analytics'))  # Redirect to view analytics after creation
        return render_template('shorten.html')  # Render the URL shortening form
    return redirect(url_for('login'))

@app.route('/view-analytics', methods=['GET'])
def view_analytics():
    if 'username' in session:
        # Fetch all links for viewing
        links = Link.query.all()
        return render_template('analytics.html', links=links)
    return redirect(url_for('login'))


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
