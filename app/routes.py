from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    """Index page - Hello World"""
    return render_template('index.html', title='Index')

@main_bp.route('/czonehome')
def czonehome():
    """Czonehome page - Hello World"""
    return render_template('czonehome.html', title='Czonehome')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login form"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.get_or_none(User.username == username)
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Logged in successfully', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', title='Login')

@main_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Simple registration form"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required', 'danger')
        elif User.get_or_none(User.username == username):
            flash('Username already taken', 'danger')
        else:
            user = User(username=username)
            user.set_password(password)
            user.save()
            flash('Registration successful; you may log in now', 'success')
            return redirect(url_for('main.login'))
    return render_template('register.html', title='Register')
