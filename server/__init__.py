# Import flask and template operators
from flask import Flask, render_template, request
from flask_mongoengine import MongoEngine
from wtforms import Form, BooleanField, StringField, PasswordField, validators
import datetime

# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_object('config')

# Database Connection
db = MongoEngine(app)

# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return '404 not found', 404


@app.route('/')
def index():
    return render_template('index.html')


##############
## Employees
#########

## ** Employee Class ** ##
class Employee(db.Document):
    first_name = db.StringField(required=True, max_length=200)
    last_name = db.StringField(required=True, max_length=200)
    department = db.StringField(required=True, max_length=200)
    code = db.StringField(required=True, max_length=20)
    date_creation = db.DateTimeField(default=datetime.datetime.utcnow)
 

## ** forms ** ##
# TODO: use model_form instead
class EmployeeForm(Form):
    first_name = StringField('First Name', [validators.Length(min=4, max=25)])
    last_name = StringField('Last Name', [validators.Length(min=4, max=25)])
    department = StringField('Department', [validators.Length(min=4, max=25)])
    code = StringField('Code', [validators.Length(min=5, max=35)])

## ** routes ** ##

# List All employees
@app.route('/employee/list/<int:page>')
def list_employee(page=1):
    employees = Employee.objects.paginate(page=page, per_page=10)
    return render_template('employees/list.html', employees=employees)

# Add new employee
@app.route('/employee/add', methods=['GET', 'POST'])
def add_employee():
    form = EmployeeForm(request.form)
    if request.method == 'POST' and form.validate():
        e = Employee(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            department=form.department.data,
            code=form.code.data
        )
        e.save()
        return "ok"
    return render_template('employees/add.html', form=form)

# Show employee by ID
@app.route('/employee/show/i/<employee_id>')
def show_employee(employee_id):
    employee = Employee.objects.get_or_404(id=employee_id)
    return render_template('employees/show.html', employee=employee)

##############
## End Employees
#########
