from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import random
import os
import uuid
import datetime
import csv
import json
import itertools
from functools import wraps
from io import StringIO
import copy
from markdown import markdown
from markupsafe import Markup
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)


# ensure the instance directory exists
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir  = os.path.join(basedir, 'instance')
os.makedirs(db_dir, exist_ok=True)

# point SQLite at instance/users.db
db_path = os.path.join(db_dir, 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --------------------------------------------------------------------
# MODELS
# --------------------------------------------------------------------
class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role     = db.Column(db.String(20), nullable=False) 

class Project(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), unique=True, nullable=False)
    base_data  = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.String(80), nullable=False)      
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                           onupdate=datetime.datetime.utcnow)

class ProjectUser(db.Model):
    id                 = db.Column(db.Integer, primary_key=True)
    project_id         = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    username           = db.Column(db.String(80), nullable=False)
    user_data          = db.Column(db.Text, nullable=False)
    created_at         = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at         = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                           onupdate=datetime.datetime.utcnow)
    project            = db.relationship('Project', backref=db.backref('project_users', lazy=True))

# --------------------------------------------------------------------
# CREATE TABLES & SEED
# --------------------------------------------------------------------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        # One superadmin
        admin_user = User(name="Admin Person", username="admin", password="admin_super@arena.14JSL", role="superadmin")
        # Example regular users
        user1 = User(name="Abdul (Test User)", username="abdul", password="expert_user@arena.1st", role="user")
        editor1 = User(name="Maziyar Panahi", username="maziyar", password="editor_mz@arena.1st", role="editor")
        db.session.add_all([admin_user, user1, editor1])
        #db.session.add_all([admin_user])
        db.session.commit()

# --------------------------------------------------------------------
# HELPERS & DECORATORS
# --------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Only superadmin can manage users and global reset
def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session or session.get("role") != "superadmin":
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Editors and superadmin can upload projects and view their own results
def editor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session or session.get("role") not in ["editor", "superadmin"]:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def user_has_completed_project(data):
    question_pool = data.get('question_pool', [])
    model_pairs   = data.get('model_pairs', [])
    current_pair_index = data.get('current_pair_index', 0)

    if question_pool:
        return False
    if current_pair_index < len(model_pairs) - 1:
        return False
    return True

# --------------------------------------------------------------------
# AUTH ROUTES (signup, login, change_password remain open to all)
# --------------------------------------------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not fullname or not username or not password:
            return render_template('signup.html', error="All fields are required.")
        if User.query.filter_by(username=username).first():
            return render_template('signup.html', error="Username already exists.")
        new_user = User(name=fullname, username=username, password=password, role='user')
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('signup_success'))
    return render_template('signup.html')

@app.route('/signup_success')
def signup_success():
    return render_template('signup_success.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            session['role'] = user.role
            return redirect(url_for('projects'))
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# change password for editor and user on signup page
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        full_name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()

        if not full_name or not username or not current_password or not new_password:
            error = "All fields are required."
            return render_template('change_password.html', error=error)

        user = User.query.filter_by(username=username, name=full_name).first()
        if not user or user.password != current_password:
            error = "Invalid credentials. Please check your name, username, and current password."
            return render_template('change_password.html', error=error)

        user.password = new_password
        db.session.commit()
        message = "Password changed successfully. Please log in with your new password."
        return render_template('change_password.html', message=message)

    return render_template('change_password.html')

# --------------------------------------------------------------------
# SUPERADMIN USER MANAGEMENT ROUTES
# --------------------------------------------------------------------
@app.route('/admin/users')
@superadmin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/add_user', methods=['GET', 'POST'])
@superadmin_required
def add_user():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role     = request.form.get('role', 'user').strip()  
        if not name or not username or not password:
            error = "All fields are required."
            return render_template('admin_add_user.html', error=error)
        if User.query.filter_by(username=username).first():
            error = "Username already exists."
            return render_template('admin_add_user.html', error=error)
        new_user = User(name=name, username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('admin_users'))
    return render_template('admin_add_user.html')

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@superadmin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user and user.username != "admin":
        ProjectUser.query.filter_by(username=user.username).delete()
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin_users'))

# Change Superadmin Password
@app.route('/admin/change_password', methods=['GET', 'POST'])
@superadmin_required
def change_superadmin_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()

        if not current_password or not new_password:
            error = "Both current and new passwords are required."
            return render_template('admin_change_password.html', error=error)

        admin_user = User.query.filter_by(username="admin").first()

        if not admin_user or admin_user.password != current_password:
            error = "Current password is incorrect."
            return render_template('admin_change_password.html', error=error)

        admin_user.password = new_password
        db.session.commit()
        message = "Password changed successfully."
        return render_template('admin_change_password.html', message=message)

    return render_template('admin_change_password.html')

# Change Editor and User Password
@app.route('/admin/reset_password/<int:user_id>', methods=['GET', 'POST'])
@superadmin_required
def admin_reset_password(user_id):
    user = db.session.get(User, user_id)
    if not user or user.username == "admin":
        return redirect(url_for('admin_users'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        if not new_password:
            error = "New password is required."
            return render_template('admin_reset_password.html', error=error, user=user)
        user.password = new_password
        db.session.commit()
        message = f"Password for user '{user.username}' has been reset successfully."
        return render_template('admin_reset_password.html', message=message, user=user)
    
    return render_template('admin_reset_password.html', user=user)

@app.route('/admin/delete_score/<int:pu_id>', methods=['POST'])
@login_required
def delete_score(pu_id):
    pu = db.session.get(ProjectUser, pu_id)
    if not pu:
        return redirect(url_for('results'))
    
    project = db.session.get(Project, pu.project_id)
    if not project:
        return redirect(url_for('results'))

    if session.get('role') == 'superadmin' or (
        session.get('role') == 'editor' and project.created_by == session['username']
    ):
        db.session.delete(pu)
        db.session.commit()
    
    return redirect(url_for('results'))

# --------------------------------------------------------------------
# HOME & PROJECTS
# --------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html', show_upload=False)

@app.route('/projects')
@login_required
def projects():
    role = session.get('role')

    if role == 'superadmin':
        projects = Project.query.order_by(Project.created_at.desc()).all()
    elif role == 'editor':
        projects = (
            Project.query
                   .filter_by(created_by=session['username'])
                   .order_by(Project.created_at.desc())
                   .all()
        )
    else:
        projects = Project.query.order_by(Project.created_at.desc()).all()

    project_available = len(projects) > 0

    return render_template(
        'projects.html',
        role=role,
        project_available=project_available,
        projects=projects
    )


# --------------------------------------------------------------------
# UPLOAD (Editors & Superadmin)
# --------------------------------------------------------------------
@app.route('/upload', methods=['POST'])
@editor_required
def upload():
    global temp_csv_data
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and file.filename.endswith('.csv'):
        temp_csv_data = pd.read_csv(file)
        return render_template('upload_confirm.html')
    return redirect(request.url)

@app.route('/confirm_upload', methods=['POST'])
@editor_required
def confirm_upload():
    global temp_csv_data
    if temp_csv_data is None:
        return redirect(url_for('projects'))

    project_name = request.form.get('project_name', '').strip()
    if not project_name:
        return "Project name is required.", 400

    df = temp_csv_data

    if len(df.columns) > 4:
        df = df.iloc[:, :4]
    models = df.columns[1:].tolist()

    valid_indices = []
    for i in range(len(df)):
        question = str(df.iloc[i, 0]).strip()
        if not df.iloc[i, 1:].isna().any() and len(question.split()) > 1:
            valid_indices.append(i)
    question_pool      = valid_indices
    model_pairs        = list(itertools.combinations(models, 2))
    current_pair_index = 0
    results            = {m: 0 for m in models}

    base_data = {
        'responses_df':      df.to_json(orient='split'),
        'models':            models,
        'question_pool':     question_pool,
        'model_pairs':       model_pairs,
        'current_pair_index':current_pair_index,
        'results':           results,
        'session_id':        str(uuid.uuid4()),
        'comparisons_made':  0,
        'results_log':       [],
        'model_pairs_completed': []
    }

    new_project = Project(
        name       = project_name,
        base_data  = json.dumps(base_data),
        created_by = session['username']
    )
    db.session.add(new_project)
    db.session.commit()

    temp_csv_data = None

    return redirect(url_for('projects'))


# --------------------------------------------------------------------
# REMOVE PROJECT (Editors & Superadmin)
# --------------------------------------------------------------------
@app.route('/remove_project/<project_name>', methods=['POST'])
@editor_required
def remove_project(project_name):
    project = Project.query.filter_by(name=project_name).first()
    if not project:
        return redirect(url_for('projects'))
    if session.get('role') == 'editor' and project.created_by != session['username']:
        return redirect(url_for('projects'))
    ProjectUser.query.filter_by(project_id=project.id).delete()
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('projects'))

# --------------------------------------------------------------------
# PROJECT SELECTION
# --------------------------------------------------------------------
@app.route('/select_project/<project_name>')
@login_required
def select_project(project_name):
    username = session.get('username')
    project = Project.query.filter_by(name=project_name).first()
    if not project:
        return redirect(url_for('projects'))

    if session.get('role') == 'admin':
        session['selected_project'] = project_name
        return redirect(url_for('arena'))

    project_user = ProjectUser.query.filter_by(project_id=project.id, username=username).first()
    if project_user:
        data = json.loads(project_user.user_data)
        if user_has_completed_project(data):
            session['selected_project'] = project_name
            return render_template('already_voted.html', project_name=project_name)
    else:
        base_data = json.loads(project.base_data)
        new_user_data = copy.deepcopy(base_data)
        project_user = ProjectUser(
            project_id=project.id,
            username=username,
            user_data=json.dumps(new_user_data)
        )
        db.session.add(project_user)
        db.session.commit()

    session['selected_project'] = project_name
    return redirect(url_for('arena'))

def _group_numbered_details(text: str) -> str:
    """
    Turn this:
       1. Anxiety Disorders:
       2. Adjusted odds ratio (aOR) = 2.13
       3. Predominated in the 12‑month period …
       5. Depressive Disorders:
       6. Adjusted odds ratio (aOR) = 2.00
       7. Twice as likely …
    Into this:
       1. Anxiety Disorders:
           1. Adjusted odds ratio (aOR) = 2.13
           2. Predominated in the 12‑month period …
       2. Depressive Disorders:
           1. Adjusted odds ratio (aOR) = 2.00
           2. Twice as likely …
    """
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        m = re.match(r'^\s*(\d+)\.\s+(.*?:)\s*$', lines[i])
        if m:
            top_idx = int(m.group(1))
            title   = m.group(2)
            out.append(f"{top_idx}. {title}")
            i += 1
            details = []
            while i < len(lines):
                m2 = re.match(r'^\s*(\d+)\.\s+(.*)$', lines[i])
                if m2 and int(m2.group(1)) > top_idx:
                    details.append(m2.group(2))
                    i += 1
                else:
                    break
            for j, detail in enumerate(details, start=1):
                out.append(f"    {j}. {detail}")
            continue

        out.append(lines[i])
        i += 1

    return "\n".join(out)

# --------------------------------------------------------------------
# ARENA (Voting)
# --------------------------------------------------------------------
@app.route('/arena')
@login_required
def arena():
    project_name = request.args.get('project')
    if project_name:
        session['selected_project'] = project_name
    else:
        project_name = session.get('selected_project')
    if not project_name:
        return redirect(url_for('projects'))

    project = Project.query.filter_by(name=project_name).first()
    if not project:
        return redirect(url_for('projects'))

    if session.get('role') == 'admin':
        data = json.loads(project.base_data)
    else:
        project_user = ProjectUser.query.filter_by(project_id=project.id, username=session['username']).first()
        if not project_user:
            return redirect(url_for('select_project', project_name=project_name))
        data = json.loads(project_user.user_data)

    responses_df = pd.read_json(StringIO(data['responses_df']), orient='split')
    question_pool = data['question_pool']
    model_pairs = data['model_pairs']
    current_pair_index = data['current_pair_index']

    if not question_pool:
        if current_pair_index < len(model_pairs) - 1:
            data['current_pair_index'] += 1
            new_pool = []
            for i in range(len(responses_df)):
                question = str(responses_df.iloc[i, 0]).strip()
                if not responses_df.iloc[i, 1:].isna().any() and len(question.split()) > 1:
                    new_pool.append(i)
            data['question_pool'] = new_pool
            if session.get('role') == 'admin':
                project.base_data = json.dumps(data)
            else:
                project_user.user_data = json.dumps(data)
            db.session.commit()
            return redirect(url_for('arena'))
        else:
            if session.get('role') == 'admin':
                return redirect(url_for('results'))
            else:
                return render_template('done.html')

    question_idx = random.choice(question_pool)
    question = responses_df.iloc[question_idx, 0]
    if len(str(question).split()) <= 1:
        question_pool.remove(question_idx)
        data['question_pool'] = question_pool
        if session.get('role') == 'admin':
            project.base_data = json.dumps(data)
        else:
            project_user.user_data = json.dumps(data)
        db.session.commit()
        return redirect(url_for('arena'))

    left_model, right_model = model_pairs[current_pair_index]
    left_response = responses_df.iloc[question_idx][left_model]
    right_response = responses_df.iloc[question_idx][right_model]
    if pd.isna(left_response) or pd.isna(right_response):
        question_pool.remove(question_idx)
        data['question_pool'] = question_pool
        if session.get('role') == 'admin':
            project.base_data = json.dumps(data)
        else:
            project_user.user_data = json.dumps(data)
        db.session.commit()
        return redirect(url_for('arena'))

    session['current_comparison'] = {
        'question_idx': question_idx,
        'model_a': left_model,
        'model_b': right_model,
        'left_model': left_model,
        'right_model': right_model,
        'project_name': project_name
    }

    valid_questions_count = len([
        i for i in range(len(responses_df))
        if not responses_df.iloc[i, 1:].isna().any() and len(str(responses_df.iloc[i, 0]).split()) > 1
    ])
    total_comparisons = len(model_pairs) * valid_questions_count
    comparisons_made = data['comparisons_made']
    progress_percentage = (comparisons_made / total_comparisons) * 100 if total_comparisons else 0

    if session.get('role') == 'admin':
        project.base_data = json.dumps(data)
    else:
        project_user.user_data = json.dumps(data)
    db.session.commit()

    clean_left  = _group_numbered_details(str(left_response))
    clean_right = _group_numbered_details(str(right_response))

    left_response_html = Markup(markdown(
        clean_left,
        extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.sane_lists',
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite'
        ]
    ))
    right_response_html = Markup(markdown(
        clean_right,
        extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.sane_lists',
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite'
        ]
    ))
    question_html = Markup(markdown(
        str(question),
        extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.sane_lists',
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite'
        ]
    ))

    return render_template('arena.html',
                           question=question_html,
                           left_response=left_response_html,
                           right_response=right_response_html,
                           left_label="Model A",
                           right_label="Model B",
                           comparison_count=comparisons_made + 1,
                           progress_percentage=progress_percentage)


# --------------------------------------------------------------------
# REDO VOTING (User can vote again on a project)
# --------------------------------------------------------------------
@app.route('/redo_voting')
@login_required
def redo_voting():
    project_name = session.get('selected_project')
    if not project_name:
        return redirect(url_for('projects'))
    project = Project.query.filter_by(name=project_name).first()
    if not project:
        return redirect(url_for('projects'))
    project_user = ProjectUser.query.filter_by(project_id=project.id, username=session['username']).first()
    if project_user:
        base_data = json.loads(project.base_data)
        new_user_data = copy.deepcopy(base_data)
        project_user.user_data = json.dumps(new_user_data)
        db.session.commit()
    return redirect(url_for('arena'))


# --------------------------------------------------------------------
# FINISH VOTING (User can forcibly exit a project)
# --------------------------------------------------------------------
@app.route('/finish_voting')
@login_required
def finish_voting():
    project_name = session.get('selected_project')
    if not project_name:
        return redirect(url_for('projects'))
    project = Project.query.filter_by(name=project_name).first()
    if not project:
        return redirect(url_for('projects'))

    if session.get('role') == 'admin':
        return redirect(url_for('results'))

    project_user = ProjectUser.query.filter_by(project_id=project.id, username=session['username']).first()
    if not project_user:
        return redirect(url_for('select_project', project_name=project_name))

    data = json.loads(project_user.user_data)
    if data['question_pool']:
        return render_template('incomplete_voting.html', project_name=project_name)
    if data['current_pair_index'] < len(data['model_pairs']) - 1:
        return render_template('incomplete_voting.html', project_name=project_name)
    return render_template('done.html')


# --------------------------------------------------------------------
# VOTE
# --------------------------------------------------------------------
@app.route('/vote', methods=['POST'])
@login_required
def vote():
    project_name = session.get('selected_project')
    if not project_name:
        return redirect(url_for('projects'))
    project = Project.query.filter_by(name=project_name).first()
    if not project:
        return redirect(url_for('projects'))

    if 'current_comparison' not in session:
        return redirect(url_for('arena'))

    if session.get('role') != 'admin':
        project_user = ProjectUser.query.filter_by(project_id=project.id, username=session['username']).first()
        if not project_user:
            return redirect(url_for('select_project', project_name=project_name))
        data = json.loads(project_user.user_data)
    else:
        data = json.loads(project.base_data)

    winner = request.form.get('choice')
    if winner not in ['left', 'right', 'tie']:
        return redirect(url_for('arena'))

    comp = session['current_comparison']
    winning_model = None
    if winner == 'left':
        winning_model = comp['left_model']
    elif winner == 'right':
        winning_model = comp['right_model']

    if winning_model:
        data['results'][winning_model] += 1

    data['results_log'].append({
        'timestamp': datetime.datetime.now().isoformat(),
        'question_idx': comp['question_idx'],
        'model_a': comp['model_a'],
        'model_b': comp['model_b'],
        'winner': winning_model if winning_model else 'tie'
    })

    qpool = data['question_pool']
    if comp['question_idx'] in qpool:
        qpool.remove(comp['question_idx'])
    data['question_pool'] = qpool

    data['comparisons_made'] += 1

    if session.get('role') == 'admin':
        project.base_data = json.dumps(data)
    else:
        project_user.user_data = json.dumps(data)

    db.session.commit()
    return redirect(url_for('arena'))

# --------------------------------------------------------------------
# DOWNLOAD RESULTS CSV (Editors own only; Superadmin all)
# --------------------------------------------------------------------
@app.route('/download_csv/<int:project_id>')
@editor_required
def download_csv(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return redirect(url_for('projects'))
    if session.get('role') == 'editor' and project.created_by != session['username']:
        return redirect(url_for('projects'))

    uploader_username = project.created_by
    uploader = User.query.filter_by(username=uploader_username).first()
    uploader_name = uploader.name if uploader else uploader_username

    base_data = json.loads(project.base_data)
    models    = base_data.get('models', [])

    all_user_results = []
    for pu in ProjectUser.query.filter_by(project_id=project_id).all():
        user = User.query.filter_by(username=pu.username).first()
        display_name = user.name if user else pu.username

        data         = json.loads(pu.user_data)
        user_results = data.get('results', {})

        total_comparisons = sum(user_results.get(m, 0) for m in models)

        row = {}
        if session.get('role') == 'superadmin':
            row['Uploaded By'] = uploader_name

        row['User'] = display_name

        for m in models:
            row[f'{m} Score'] = user_results.get(m, 0)
        for m in models:
            pct = (user_results.get(m, 0) / total_comparisons * 100) if total_comparisons else 0.0
            row[f'{m} Percentage'] = round(pct, 1)

        row['Total Comparisons'] = total_comparisons
        all_user_results.append(row)

    score_cols      = [f'{m} Score' for m in models]
    percentage_cols = [f'{m} Percentage' for m in models]
    tail_cols       = ['Total Comparisons']

    if session.get('role') == 'superadmin':
        columns = ['Uploaded By', 'User'] + score_cols + percentage_cols + tail_cols
    else:
        columns = ['User'] + score_cols + percentage_cols + tail_cols

    df = pd.DataFrame(all_user_results, columns=columns)
    csv_data = df.to_csv(index=False, quoting=csv.QUOTE_NONNUMERIC)
    filename = f"results_{project.name}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


# --------------------------------------------------------------------
# DOWNLOAD DETAILED RESULTS CSV (Editors own only; Superadmin all)
# --------------------------------------------------------------------
@app.route('/download_detailed_csv/<int:project_id>')
@editor_required
def download_detailed_csv(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return redirect(url_for('projects'))
    if session.get('role') == 'editor' and project.created_by != session['username']:
        return redirect(url_for('projects'))

    uploader = User.query.filter_by(username=project.created_by).first()
    uploader_name = uploader.name if uploader else project.created_by

    base_data = json.loads(project.base_data)
    responses_df = pd.read_json(StringIO(base_data['responses_df']), orient='split')

    logs = []
    for pu in ProjectUser.query.filter_by(project_id=project_id).all():
        user = User.query.filter_by(username=pu.username).first()
        display_name = user.name if user else pu.username
        data = json.loads(pu.user_data)

        for entry in data.get('results_log', []):
            qi = entry['question_idx']
            ma = entry['model_a']
            mb = entry['model_b']

            row = {}
            if session.get('role') == 'superadmin':
                row['Uploaded By'] = uploader_name

            row.update({
                'User': display_name,
                'Question Index': qi,
                'Question': responses_df.iloc[qi, 0],
                'Model A': ma,
                'Model A Response': responses_df.iloc[qi][ma],
                'Model B': mb,
                'Model B Response': responses_df.iloc[qi][mb],
                'Winner': entry['winner']
            })

            logs.append(row)

    base_cols = [
        'User',
        'Question Index',
        'Question',
        'Model A',
        'Model A Response',
        'Model B',
        'Model B Response',
        'Winner'
    ]
    if session.get('role') == 'superadmin':
        columns = ['Uploaded By'] + base_cols
    else:
        columns = base_cols

    df = pd.DataFrame(logs, columns=columns)
    csv_data = df.to_csv(index=False, quoting=csv.QUOTE_NONNUMERIC)
    filename = f"detailed_results_{project.name}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

# --------------------------------------------------------------------
# RESULTS (Editors see only own; Superadmin sees all)
# --------------------------------------------------------------------
@app.route('/results')
@editor_required
def results():
    role = session.get('role')
    if role == 'superadmin':
        projects = Project.query.order_by(Project.created_at.desc()).all()
    else:
        projects = (
            Project.query
                   .filter_by(created_by=session['username'])
                   .order_by(Project.created_at.desc())
                   .all()
        )

    all_projects_results = []
    for p in projects:
        user_results = []
        for pu in ProjectUser.query.filter_by(project_id=p.id).all():
            user_obj     = User.query.filter_by(username=pu.username).first()
            display_name = user_obj.name if user_obj else pu.username
            data         = json.loads(pu.user_data)

            results       = data.get('results', {})
            total_votes   = sum(results.values())
            win_percentages = {
                m: (results.get(m, 0) / total_votes * 100) if total_votes else 0.0
                for m in data.get('models', [])
            }
            sorted_models = sorted(win_percentages.items(), key=lambda x: x[1], reverse=True)

            pairwise = {}
            for entry in data.get('results_log', []):
                ma, mb, winner = entry['model_a'], entry['model_b'], entry['winner']
                key = f"{ma} vs {mb}"
                if key not in pairwise:
                    pairwise[key] = {'total':0, ma:0, mb:0, 'tie':0}
                pairwise[key]['total'] += 1
                if winner in [ma, mb]:
                    pairwise[key][winner] += 1
                else:
                    pairwise[key]['tie'] += 1

            user_results.append({
                'username': display_name,
                'session_id': data.get('session_id'),
                'comparisons_made': data.get('comparisons_made', 0),
                'sorted_models': sorted_models,
                'pairwise_results': pairwise,
                'project_user_id': pu.id
            })

        all_projects_results.append({
            'project_name': p.name,
            'project_id':   p.id,
            'user_results': user_results
        })

    return render_template('results.html', all_projects_results=all_projects_results)

# --------------------------------------------------------------------
# RESET ALL (Superadmin only)
# --------------------------------------------------------------------
@app.route('/reset_all')
@superadmin_required
def reset_all():
    ProjectUser.query.delete()
    Project.query.delete()
    db.session.commit()
    session.pop('selected_project', None)
    return redirect(url_for('projects'))

# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

