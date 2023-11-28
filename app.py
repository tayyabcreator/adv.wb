from flask import Flask, render_template, url_for, redirect , request , flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import secrets
import os
from datetime import datetime, timedelta
from flask import send_from_directory

app = Flask(__name__)

bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Todo(db.Model):
    task_id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    date=db.Column(db.String(100))
    done=db.Column(db.Boolean)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
                username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                    'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


@app.route('/')
def home():
    return render_template('home.html')


def get_task_with_least_time():
    pending_tasks = Todo.query.filter_by(done=False).all()

    if pending_tasks:
        current_date = datetime.now().date()

        # Initialize variables to track the task with the least time left
        min_time_task = None
        min_time_left = timedelta.max

        for task in pending_tasks:
            due_date = datetime.strptime(task.date, '%Y-%m-%d').date()
            time_left = due_date - current_date

            # Update the minimum time task if a task has less time left
            if time_left < min_time_left:
                min_time_left = time_left
                min_time_task = task

        return min_time_task, min_time_left.days if min_time_task else None

    return None, None
@app.route('/add', methods=['POST'])
def add():
    name = request.form.get("taskname")
    date = request.form.get("duedate")

    # Convert the date string to a datetime object for comparison
    due_date = datetime.strptime(date, '%Y-%m-%d').date()
    current_date = datetime.now().date()

    if due_date < current_date:
        # Handle the case where the due date is earlier than the current date
        flash('Due date cannot be earlier than the current date')
        return redirect(url_for('dashboard'))

    new_task = Todo(name=name, date=date, done=False)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for("dashboard"))


@app.route('/update/<int:todo_id>')
def update(todo_id):
    todo= Todo.query.get(todo_id)
    todo.done=not todo.done
    db.session.commit()
    return redirect(url_for("dashboard"))


@app.route('/delete/<int:todo_id>')
def delete(todo_id):
    todo= Todo.query.get(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route('/time_left/<int:todo_id>')
def time_left(todo_id):
    todo = Todo.query.get(todo_id)
    if todo.date:
        due_date = datetime.strptime(todo.date, '%Y-%m-%d').date()
        current_date = datetime.now().date()
        time_left = due_date - current_date

        if time_left.days > 1:
            return f"{time_left.days} days"
        elif time_left.days == 1:
            return "1 day"
        # elif time_left.days == 0:
        #     # Calculate hours if less than a day is left
        #     hours_left = (due_date - datetime.now()).seconds // 3600
        #     return f"{hours_left} hours"
        else:
            return "Task expired"
    return "No due date set"


upload_folder = os.path.join("static","uploads")
app.config['UPLOAD_FOLDER'] = upload_folder  # Use 'UPLOAD_FOLDER' instead of 'UPLOAD'

@app.route('/Upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['img']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path.replace("\\","/"))
            todo_list=Todo.query.all()
            upcoming_task, days_left = get_task_with_least_time()
            return render_template('dashboard.html',todo_list=todo_list,upcoming_task=upcoming_task, days_left=days_left , time_left=time_left,img=file_path)
    return render_template('index.html')




def get_closest_task():
    todo_list = Todo.query.all()

    # Get tasks with due dates and calculate time left
    tasks_with_due_dates = [task for task in todo_list if task.date]
    current_date = datetime.now().date()

    # Sort tasks based on time left (ascending order)
    sorted_tasks = sorted(tasks_with_due_dates, key=lambda x: datetime.strptime(x.date, '%Y-%m-%d').date() - current_date)

    # Select the task with the least time left (first in the sorted list)
    if sorted_tasks:
        return sorted_tasks[0], (datetime.strptime(sorted_tasks[0].date, '%Y-%m-%d').date() - current_date)
    else:
        return None, None




@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('loginv1.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    upcoming_task, days_left = get_task_with_least_time()
    todo_list = Todo.query.all()
    return render_template('dashboard.html', todo_list=todo_list, upcoming_task=upcoming_task, days_left=days_left ,time_left=time_left)



@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


if __name__ == "__main__":
    app.run(debug=True)

