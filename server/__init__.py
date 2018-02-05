# Import flask and template operators
from flask import Flask, render_template, request
from wtforms import Form, BooleanField, StringField, PasswordField, validators

# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_object('config')

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
## ** forms ** ##
class newEmployeeForm(Form):
    first_name = StringField('First Name', [validators.Length(min=4, max=25)])
    last_name = StringField('Last Name', [validators.Length(min=4, max=25)])
    departement = StringField('Departement', [validators.Length(min=4, max=25)])
    code = StringField('Code', [validators.Length(min=5, max=35)])


## ** routes ** ##

# List All employees
@app.route('/employee/list')
def list_employee():
    return render_template('employees/list.html')

# Add new employee
@app.route('/employee/add', methods=['GET', 'POST'])
def add_employee():
    form = newEmployeeForm(request.form)
    if request.method == 'POST' and form.validate():
        return "hi"
    return render_template('employees/add.html', form=form)



##############
## End Employees
#########
