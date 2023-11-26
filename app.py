from flask import Flask, flash,render_template,request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import secrets
import os
from datetime import datetime, timedelta
from flask import send_from_directory

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db= SQLAlchemy(app)

app.secret_key = secrets.token_hex(16)
class Todo(db.Model):
    task_id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    date=db.Column(db.String(100))
    done=db.Column(db.Boolean)

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


@app.route('/')
def home():
    upcoming_task, days_left = get_task_with_least_time()
    todo_list = Todo.query.all()
    return render_template('index.html', todo_list=todo_list, upcoming_task=upcoming_task, days_left=days_left ,time_left=time_left)

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
        return redirect(url_for('home'))

    new_task = Todo(name=name, date=date, done=False)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for("home"))


@app.route('/update/<int:todo_id>')
def update(todo_id):
    todo= Todo.query.get(todo_id)
    todo.done=not todo.done
    db.session.commit()
    return redirect(url_for("home"))


@app.route('/delete/<int:todo_id>')
def delete(todo_id):
    todo= Todo.query.get(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("home"))

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


upload = 'C:/Users/HP/Downloads/todo_app-main/todo_app-main/Upload'
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
            return render_template('index.html',todo_list=todo_list,upcoming_task=upcoming_task, days_left=days_left , time_left=time_left,img=file_path)
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
    

if __name__=='__main__':
    app.run(debug=False)
