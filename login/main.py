from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from toignore import key
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure Database Model
# app.config['SQLALCHEMY_DATABASE_URI'] = (f'postgresql+psycopg2://postgres:{key}@localhost:5432/user_psg')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Database Model
class User(db.Model):
    # class variable
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(1500), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MyTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100), nullable=False)
    complete = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"Task {self.id}"

with app.app_context():
    db.create_all()

# routes
@app.get("/")
def home():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")

# login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            return  redirect(url_for("dashboard"))
        else:
            print(user)
            # add a error to indicate username already exits: even old username with newpassword registration gives error
            return render_template("index.html", error='Invalid username or password')
    return render_template("index.html")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template("index.html", error="User already registered!!")
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect(url_for('dashboard'))
    return render_template("index.html")


# Dashboard
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "username" not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        current_task = request.form['content']
        new_task = MyTask(content=current_task)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('dashboard'))

    tasks = MyTask.query.order_by(MyTask.created).all()
    return  render_template('dashboard.html', tasks=tasks, username=session['username'])

# logout
@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


# delete an Item
@app.route("/dashboard/delete/<int:id>")
def delete(id:int):
    delete_task = MyTask.query.get_or_404(id)
    try:
        db.session.delete(delete_task)
        db.session.commit()
        return redirect(url_for('dashboard'))
    except Exception as e:
        return f"ERROR: {e}"


# update an Item
@app.route("/dashboard/edit/<int:id>", methods=["GET", "POST"])
def update(id: int):
    task = MyTask.query.get_or_404(id)
    if request.method == "POST":
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect(url_for('dashboard'))
        except Exception as e:
            return f"ERROR: {e}"
    else:
        return render_template('edit.html', task=task)


if __name__ == "__main__":
    app.run(debug=True)