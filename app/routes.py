from flask import Blueprint, render_template

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
