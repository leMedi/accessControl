# Import flask and template operators
from flask import Flask, render_template, request, redirect
from flask_mongoengine import MongoEngine
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from wtforms_components import TimeField
import datetime
import coloredlogs
import logging
# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_object('config')

# Database Connection
db = MongoEngine(app)

##############
## Logger
#########
# Create a logger object.
logger = logging.getLogger('FLASK')
coloredlogs.install(level='DEBUG', logger=logger)
logger.debug("Logger running")

##############
## End Logger
#########

##############
## Jinja Filters
#########
# convert hour:minute timestamp to HH:MM string
def pretty_print_time(value):
    # bug in datetime cannot convert from timestamp 0 (https://github.com/home-assistant/appdaemon/issues/83)
    delta = 86400
    d = datetime.datetime.fromtimestamp(delta + value)
    return d.strftime('%H:%M')


app.jinja_env.filters['datetime'] = pretty_print_time


# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return '404 not found', 404


@app.route('/')
def index():
    return render_template('index.html')


##############
## Badges
#########
## ** Employee Class ** ##
class Badge(db.EmbeddedDocument):
    code_hex = db.StringField(required=True, max_length=15)
    code_dec = db.StringField(max_length=15)
    is_active = db.BooleanField(required=True, default=True)
    owner = db.ObjectIdField(required=True)
    date_creation = db.DateTimeField(default=datetime.datetime.utcnow)

## ** forms ** ##
class BadgeForm(Form):
    code_hex = StringField('Badge Code', [validators.Length(min=4, max=25)])

# delete badge by hexCode
@app.route('/badge/delete/h/<badge_hexcode>/<employee_id>')
def add_badge(employee_id, badge_hexcode):
    Employee.objects(id=employee_id).update(
        pull__badges__code_hex=badge_hexcode)
    return redirect("/employee/show/i/" + employee_id)

##############
## End Badges
#########

##############
## Employees
#########

## ** Employee Class ** ##
class Employee(db.Document):
    first_name = db.StringField(required=True, max_length=200)
    last_name = db.StringField(required=True, max_length=200)
    department = db.StringField(required=True, max_length=200)
    code = db.StringField(unique=True, required=True, max_length=20)
    date_creation = db.DateTimeField(default=datetime.datetime.utcnow)
    badges = db.ListField(db.EmbeddedDocumentField(Badge))

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
    logger.info("Listing Employees")
    employees = Employee.objects.paginate(page=page, per_page=10)
    return render_template('employees/list.html', employees=employees, title="Employees")

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
        logger.info("New Employee added")
        return redirect("/employee/show/i/" + str(e.id))
    return render_template('employees/add.html', form=form, title="Employees")

# Show employee by ID
@app.route('/employee/show/i/<employee_id>', methods=['GET', 'POST'])
def show_employee(employee_id):
    employee = Employee.objects.get_or_404(id=employee_id)
    form = BadgeForm(request.form)
    if request.method == 'POST' and form.validate():
        b = Badge(
            code_hex=form.code_hex.data,
            owner=employee.id
        )
        employee.badges.append(b)
        employee.save()
        form = BadgeForm()
    return render_template('employees/show.html', employee=employee, form=form, title="Employees")

##############
## End Employees
#########


##############
## Access
#########
def get_day_timestamp(t):
    hour = t.hour * 3600
    minute = t.minute * 60
    return (hour + minute)


## ** Embeded Employee Class ** ##
class EmbededEmployee(db.EmbeddedDocument):
    employee_id = db.ObjectIdField(required=True)
    name = db.StringField(required=True, max_length=200)
    code = db.StringField(unique=True, required=True, max_length=20)

## ** Access Class ** ##
class Access(db.Document):
    name = db.StringField(unique=True, required=True, max_length=200)
    start_time = db.IntField(required=True)
    end_time = db.IntField(required=True)
    active = db.BooleanField(required=True, default=True)
    badges = db.ListField(db.StringField(max_length=15))
    employees = db.ListField(db.EmbeddedDocumentField(EmbededEmployee))

## ** forms ** ##
class AccessForm(Form):
    name = StringField('Name')
    start = TimeField('Start Time')
    end = TimeField('End Time') # TODO: validate end > start

## ** routes ** ##
@app.route('/access/add', methods=['GET', 'POST'])
def add_access():
    form = AccessForm(request.form)
    if request.method == 'POST' and form.validate():
        # start = datetime.datetime.strptime(form.start.data, "%H:%M")
        # end = datetime.datetime.strptime(form.end.data, "%H:%M")
        a = Access(
            name=form.name.data,
            start_time=get_day_timestamp(form.start.data),
            end_time=get_day_timestamp(form.end.data)
        )
        a.save()
        return redirect("/access/list/1")
    return render_template('access/add.html', form=form, title="Access")

# List All accesses
@app.route('/access/list/<int:page>')
def list_access(page=1):
    accesses = Access.objects.paginate(page=page, per_page=10)
    return render_template('access/list.html', accesses=accesses, title="Access")

# Show access by ID
@app.route('/access/show/i/<access_id>', methods=['GET', 'POST'])
def show_access(access_id):
    access = Access.objects.get_or_404(id=access_id)
    form = BadgeForm(request.form)
    if request.method == 'POST' and form.validate():
        employees = Employee.objects(badges__code_hex=form.code_hex.data)
        if employees.count() > 0:
            access.badges.append(form.code_hex.data)
            for employee in employees:
                e = EmbededEmployee(
                    employee_id=employee.id,
                    name=employee.last_name + ' ' + employee.first_name,
                    code=form.code_hex.data
                )
                access.employees.append(e)
            access.save()
            form = BadgeForm()
    return render_template('access/show.html', access=access, form=form, title="Access")

# delete access
@app.route('/access/delete/i/<access_id>')
def delete_access(access_id):
    Access.objects(id=access_id).delete()
    return redirect("/access/list/1")

# delete employee from access
@app.route('/access/delete/h/<badge_hexcode>/<access_id>')
def delete_employee_access(badge_hexcode, access_id):
    Access.objects(badges=badge_hexcode).update(
        pull__badges__code_hex=badge_hexcode)
    return redirect("/employee/show/i/" + badge_hexcode)

##############
## End Access
#########

##############
## Events
#########
## ** Event Class ** ##
class Event(db.Document):
    badge_hexcode = db.StringField(required=True, max_length=200)
    badge_owner = db.StringField(required=True)
    date = db.DateTimeField(default=datetime.datetime.utcnow)
    authorized = db.BooleanField(required=True, default=True)

# List events
@app.route('/events/list/<int:page>')
def list_events(page=1):
    events = Event.objects.paginate(page=page, per_page=50)
    return render_template('events/list.html', events=events, title="Events")


##############
## End Events
#########
