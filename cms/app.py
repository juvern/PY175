import os
import yaml
import bcrypt
from gen_pass import gen_pass
from markdown import markdown
from functools import wraps
from flask import (
        Flask,
        render_template,
        send_from_directory,
        session,
        flash,
        url_for,
        redirect,
        request
        )

app = Flask(__name__)
app.secret_key='secret1'

def get_data_app():
    if app.config['TESTING']:
        return os.path.join(os.path.dirname(__file__), 'tests', 'data')
    else:
        return os.path.join(os.path.dirname(__file__), 'cms', 'data')


def load_user_credentials():
    filename = 'users.yml'
    root_dir = os.path.dirname(__file__)
    if app.config['TESTING']:
        credentials_path = os.path.join(root_dir, 'tests', filename)
    else:
        credentials_path = os.path.join(root_dir, "cms", filename)

    with open(credentials_path, 'r') as file:
        return yaml.safe_load(file)

def valid_credentials(username, password):
    credentials = load_user_credentials()

    if username in credentials:
        stored_password = credentials[username].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_password)
    else:
        return False


def user_signed_in():
    return 'username' in session # True or False if key exists


def require_login(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not user_signed_in():
            flash("You must be signed in to do that.")
            return redirect(url_for('show_signin_form'))
        return func(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    data_dir = get_data_app()
    # iterate through each item in directory
    files = [os.path.basename(path) for path in os.listdir(data_dir)]

    return render_template('index.html', files=files)

@app.route('/<filename>')
def open_file(filename):
    data_dir = get_data_app()
    file_path = os.path.join(data_dir, filename)

    base, ext = os.path.splitext(file_path)

    # checks that it's an existing file
    if not os.path.isfile(file_path):
        flash(f"{filename} does not exist.", 'error')
        return redirect(url_for('index'))
    
    if ext == '.md':
        with open(file_path, 'r') as file:
            content = file.read()
            return render_template('markdown.html', content=markdown(content))
    
    return send_from_directory(data_dir, filename)

@app.route('/<filename>/edit')
@require_login
def edit_file(filename):
    data_dir = get_data_app()
    file_path = os.path.join(data_dir, filename)

    if not os.path.isfile(file_path):
        flash(f"{filename} does not exist.", 'error')
        return redirect(url_for('index'))

    with open(file_path, 'r') as file:
        content = file.read()

    return render_template('edit.html', filename=filename, content=content)


@app.route('/<filename>/edit', methods=['POST'])
@require_login
def save_file(filename):
    data_dir = get_data_app()
    file_path = os.path.join(data_dir, filename)

    if not os.path.isfile(file_path):
        flash(f"{filename} does not exist.", 'error')
        return redirect(url_for('index'))
    
    content = request.form['content']
    with open(file_path, 'w') as file:
        file.write(content)

    flash(f"{filename} has been updated.")

    return redirect(url_for('index'))


@app.route('/new')
@require_login
def new_file():
    return render_template('new.html')

@app.route('/create', methods=['POST'])
@require_login
def create_file():
    # get the name for form submission
    filename = request.form.get('filename', '').strip()
    data_dir = get_data_app()
    file_path = os.path.join(data_dir, filename)

    if len(filename) == 0:
        flash("A name is required")
        return render_template('/new.html'), 422
    elif os.path.exists(file_path):
        flash(f"{filename} already exists.")
    else:
        with open(file_path, 'w') as file:
            file.write("")

        flash(f"{filename} has been created.")
        return redirect(url_for('index'))

@app.route('/<filename>/delete', methods=['POST'])
@require_login
def delete_file(filename):
    data_dir = get_data_app()
    file_path = os.path.join(data_dir, filename)
    
    if os.path.isfile(file_path):
        os.remove(file_path)
        flash(f"{filename} has been deleted.")
    else:
        flash(f"{filename} does not exist.")

    return redirect(url_for('index'))

@app.route('/users/signin')
def show_signin_form():
    return render_template('signin.html')

@app.route('/users/signin', methods=['POST'])
def signin():
    username = request.form.get('username')
    password = request.form.get('password')

    if valid_credentials(username, password):
        flash('Welcome!')
        session['username'] = username
        return redirect(url_for('index'))

    flash('Invalid credentials')
    return render_template('signin.html', username=username, password=""),  422

@app.route("/users/signout", methods=['POST'])
def signout():
    session.pop('username', None)
    flash("You have been signed out.")
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5003)
