from flask import Flask, render_template, send_file
import subprocess
import numpy as np
import seaborn as sns
from flask import Flask, render_template, request
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask_login import login_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

import os
if not os.path.exists('tmp'):
    os.makedirs('tmp')

from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secret key for Flask sessions
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
app.logger.setLevel(logging.INFO)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    financial_data = db.relationship('FinancialData', backref='user', lazy=True)

class FinancialData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    commodity = db.Column(db.String(50), nullable=False)
    expense = db.Column(db.Float, nullable=False)
    # Add other fields as needed (e.g., date, notes)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    
class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Add other necessary fields and relationships

    def __repr__(self):
        return f"Category(name={self.name}, user_id={self.user_id})"
    
class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.utcnow)

    def __repr__(self):
        return f"Reminder(content={self.content}, due_date={self.due_date}, priority={self.priority})"


# Load data from CSV file
file_path = 'prices.csv'
data = pd.read_csv(file_path)

# Function to calculate budget
def calculate_budget(expenses):
    total_budget = sum(expenses)
    return total_budget if not pd.isna(total_budget) else 0

# Function to track expenses
def track_expenses(expense_tracker, expense):
    expense_tracker.append(expense)

# Routes
@app.route('/')
def index0():
    if current_user.is_authenticated:
        # state_list = data['state'].unique()
        # commodity_list = data['commodity'].unique()
        # return render_template('market_price_analysis.html', state_list=state_list, commodity_list=commodity_list)
        return render_template('terratech.html')
    else:
        return redirect(url_for('login'))
    
@app.route('/index')
def index():
    if current_user.is_authenticated:
        # state_list = data['state'].unique()
        # commodity_list = data['commodity'].unique()
        # return render_template('market_price_analysis.html', state_list=state_list, commodity_list=commodity_list)
        return render_template('index.html')
    else:
        return redirect(url_for('login'))
    
@app.route("/manage_expenses")
def manage_expenses():
    expenses = Expense.query.all()
    income = Income.query.all()
    budgets = Budget.query.all()
    
    return render_template('manage_expenses.html', expenses=expenses, income=income, budgets=budgets)


@app.route('/market_price_analysis')
def market_price_analysis():
    # Run R script
    subprocess.run(['Rscript', 'main.r'])
    
    return render_template('market_price_analysis.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            user = User.query.filter_by(username=username).first()

            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('terratech'))
            else:
                flash('Login failed. Please check your username and password.', 'danger')

        except Exception as e:
            app.logger.error(f"Error during login: {str(e)}")
            flash('An error occurred. Please try again later.', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password == confirm_password:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match. Please try again.', 'danger')

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/plot/<plot_name>')
def plot(plot_name):
    # Serve dynamically generated plot
    return send_file(f'tmp/{plot_name}.png', mimetype='image/png')

@app.route('/add_expense', methods=['POST'])
def add_expense():
    try:
        # Extract export details from the form
        date = request.form['date']
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']

        
        # Continue with adding the expense to the database
        expense_data = {
            'date': date,
            'amount': amount, 
            'category': category,
            'description': description
        }

        new_expense = Expense(**expense_data)
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
    except ValueError as e:
        flash(f'Error adding expense: {str(e)}', 'error')

    return redirect(url_for('manage_expenses'))

@app.route('/edit_expense/<int:index>', methods=['GET', 'POST'])
def edit_expense(index):
    expense_to_edit = Expense.query.get_or_404(index)

    if request.method == 'POST':
        try:
            expense_to_edit.date = request.form['date']
            expense_to_edit.amount = float(request.form['amount'])
            expense_to_edit.category = request.form['category']
            expense_to_edit.description = request.form['description']

            db.session.commit()
            flash('Expense edited successfully!', 'success')
            return redirect(url_for('index'))
        except ValueError as e:
            flash(f'Error editing expense: {str(e)}', 'error')

    return render_template('edit_expense.html', expense=expense_to_edit)
@app.route('/expense_tracker', methods=['GET', 'POST'])
def expense_tracker():
    if request.method == 'POST':
        try:
            expense_data = {
                'date': request.form['date'],
                'amount': float(request.form['amount']),
                'category': request.form['category'],
                'description': request.form['description']
            }
            new_expense = Expense(**expense_data)
            db.session.add(new_expense)
            db.session.commit()
            flash('Expense added successfully!', 'success')
        except ValueError as e:
            flash(f'Error adding expense: {str(e)}', 'error')

    expenses = Expense.query.all()  # Fetch expenses from the database
    return render_template('expense_tracker.html', expenses=expenses)
from flask import jsonify

@app.route('/get_budget_data', methods=['GET'])
def get_budget_data():
    # Fetch budget categories
    budget_categories = [budget_item.category for budget_item in Budget.query.all()]

    # Fetch total budget amounts for each category
    budget_amounts = [budget_item.amount for budget_item in Budget.query.all()]

    # Fetch total expense amounts for each category
    expense_amounts = []
    for category in budget_categories:
        total_expense = sum([expense.amount for expense in Expense.query.filter_by(category=category).all()])
        expense_amounts.append(total_expense)

    data = {
        'budgetLabels': budget_categories,
        'budgetAmounts': budget_amounts,
        'expenseAmounts': expense_amounts,
    }

    return jsonify(data)
@app.route('/add_income', methods=['POST'])
def add_income():
    if request.method == 'POST':
        try:
            income_data = {
                'source': request.form['source'],
                'amount': float(request.form['amount']),
                'description': request.form['description']
            }
            new_income = Income(**income_data)
            db.session.add(new_income)
            db.session.commit()
            flash('Income added successfully!', 'success')
        except ValueError as e:
            flash(f'Error adding income: {str(e)}', 'error')
    income = Income.query.all()
    return render_template('income_tracker.html', income=income)
@app.route('/add_budget', methods=['POST'])
def add_budget():
    if request.method == 'POST':
        try:
            category = request.form['category']
            amount = float(request.form['amount'])

            # Check if a budget with the given category already exists
            existing_budget = Budget.query.filter_by(category=category).first()

            if existing_budget:
                # Update the existing budget
                existing_budget.amount = amount
                flash('Budget updated successfully!', 'success')
            else:
                # Add a new budget
                new_budget = Budget(category=category, amount=amount)
                db.session.add(new_budget)
                flash('Budget added successfully!', 'success')

            db.session.commit()

        except ValueError as e:
            flash(f'Error adding/updating budget: {str(e)}', 'error')

    return redirect(url_for('budget_tracker'))
@app.route('/delete_budget/<int:index>')
def delete_budget(index):
    try:
        budgets = Budget.query.all()

        if index < 0 or index >= len(budgets):
            flash('Invalid budget index for deletion', 'error')
        else:
            budget_to_delete = budgets[index]
            db.session.delete(budget_to_delete)
            db.session.commit()
            flash('Budget deleted successfully!', 'success')

    except Exception as e:
        flash(f'Error deleting budget: {str(e)}', 'error')

    return redirect(url_for('budget_tracker'))

@app.route('/delete_expense/<int:index>')
def delete_expense(index):
    expenses = Expense.query.all()
    
    if index < 0 or index >= len(expenses):
        flash('Invalid expense index for deletion', 'error')
    else:
        expense_to_delete = expenses[index]
        db.session.delete(expense_to_delete)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')

    return redirect(url_for('index'))
@app.route('/financial_summary')
def financial_summary():
    # Fetch expenses, income, and budgets from the database
    expenses = Expense.query.all()
    income = Income.query.all()
    dynamic_categories = get_dynamic_categories()
    
    total_income = sum([item.amount for item in income])
    total_expenses = sum([item.amount for item in expenses])
    net_income = total_income - total_expenses

    return render_template('financial_summary.html', expenses=expenses, income=income,
                           categories=dynamic_categories, net_income=net_income)

def get_dynamic_categories():
    categories = Category.query.all()
    formatted_categories = []
    
    for category in categories:
        # Fetch all income entries for the given category
        income_entries = Income.query.filter_by(category=category.name).all()
        total_income = sum([income.amount for income in income_entries])
        
        # Fetch all expense entries for the given category
        expense_entries = Expense.query.filter_by(category=category.name).all()
        total_expenses = sum([expense.amount for expense in expense_entries])
        
        # Calculate net income for the category
        net_income = total_income - total_expenses
        
        formatted_categories.append({
            'name': category.name,
            'income': total_income,
            'expenses': total_expenses,
            'net_income': net_income
        })
    
    return formatted_categories

def calculate_category_income(category_id):
    # Fetch all income entries for the given category_id
    income_entries = Income.query.filter_by(category_id=category_id).all()

    # Calculate the total income for the category
    total_income = sum([income.amount for income in income_entries])

    return total_income

def calculate_category_expenses(category_id):
    # Fetch all expense entries for the given category_id
    expense_entries = Expense.query.filter_by(category_id=category_id).all()

    # Calculate the total expenses for the category
    total_expenses = sum([expense.amount for expense in expense_entries])

    return total_expenses


def calculate_category_net_income(category_id):
    # Fetch all expense entries for the given category_id
    expense_entries = Expense.query.filter_by(category_id=category_id).all()

    # Fetch all income entries for the given category_id
    income_entries = Income.query.filter_by(category_id=category_id).all()

    # Calculate the total expenses for the category
    total_expenses = sum([expense.amount for expense in expense_entries])

    # Calculate the total income for the category
    total_income = sum([income.amount for income in income_entries])

    # Calculate the net income (profit or loss)
    net_income = total_income - total_expenses

    return net_income


@app.route('/budget_tracker')
def budget_tracker():
    budgets = Budget.query.all()  # Fetch budgets from the database
    expenses = Expense.query.all()  # Fetch expenses from the database

    remaining_budgets = calculate_remaining_budget(budgets, expenses)

    return render_template('budget_tracker.html', budgets=budgets, expenses=expenses, remaining_budgets=remaining_budgets)

def calculate_remaining_budget(budgets, expenses):
    remaining_budgets = []

    # Create a dictionary to store the total expenses for each category
    category_expenses = {budget.category: 0 for budget in budgets}

    # Calculate total expenses for each category
    for expense in expenses:
        category = expense.category
        # Check if the category key exists in the dictionary
        if category in category_expenses:
            category_expenses[category] += expense.amount
        else:
            # Handle the case where the category key doesn't exist (optional)
            print(f"Warning: Category '{category}' not found in budgets.")

    # Calculate remaining budgets
    for budget in budgets:
        total_expenses = category_expenses.get(budget.category, 0)
        remaining_budget = budget.amount - total_expenses

        remaining_budgets.append({
            'category': budget.category,
            'remaining_budget': remaining_budget if remaining_budget >= 0 else 0
        })

    return remaining_budgets



@app.route('/income_tracker', methods=['GET', 'POST'])
def income_tracker():
    if request.method == 'POST':
        # Handle form submission to add income
        try:
            income_data = {
                'source': request.form['source'],
                'amount': float(request.form['amount']),
                'description': request.form['description']
            }
            Income.query.all().append(income_data)
            flash('Income added successfully!', 'success')
        except ValueError as e:
            flash(f'Error adding income: {str(e)}', 'error')
    return render_template('income_tracker.html', income=Income.query.all())
@app.route('/add_reminder', methods=['POST'])
def add_reminder():
    try:
        new_reminder = request.form.get('newReminder')
        due_date_str = request.form.get('dueDate')
        priority = request.form.get('priority')

        if not new_reminder:
            flash('Reminder content cannot be empty!', 'error')
            return redirect(url_for('reminder'))

        if due_date_str:
            try:
                due_date_obj = datetime.fromisoformat(due_date_str)
            except ValueError as e:
                flash(f"Invalid due date format. Please use YYYY-MM-DD.", 'error')
                return redirect(url_for('reminder'))

        else:
            due_date_obj = None

        new_reminder_obj = Reminder(content=new_reminder, due_date=due_date_obj, priority=priority)
        db.session.add(new_reminder_obj)
        db.session.commit()

        flash('Reminder added successfully!', 'success')
        return redirect(url_for('reminder'))

    except SQLAlchemyError as e:
        app.logger.error(f"Error adding reminder: {str(e)}")
        flash('An error occurred while adding the reminder. Please try again later.', 'error')
        return redirect(url_for('reminder'))
@app.route('/reminder', methods=['GET', 'POST'])
def reminder():
    if request.method == 'POST':
        # Handle the form submission for adding a new reminder
        try:
            new_reminder = request.form.get('newReminder')
            due_date_str = request.form.get('dueDate')
            priority = request.form.get('priority')

            if not new_reminder:
                flash('Reminder content cannot be empty!', 'error')
                return redirect(url_for('reminder'))

            if due_date_str:
                try:
                    due_date_obj = datetime.fromisoformat(due_date_str)
                except ValueError as e:
                    flash(f"Invalid due date format. Please use YYYY-MM-DD.", 'error')
                    return redirect(url_for('reminder'))

            else:
                due_date_obj = None

            new_reminder_obj = Reminder(content=new_reminder, due_date=due_date_obj, priority=priority)
            db.session.add(new_reminder_obj)
            db.session.commit()

            flash('Reminder added successfully!', 'success')
            return redirect(url_for('reminder'))

        except SQLAlchemyError as e:
            app.logger.error(f"Error adding reminder: {str(e)}")
            flash('An error occurred while adding the reminder. Please try again later.', 'error')
            return redirect(url_for('reminder'))

    else:
        # Handle the GET request for displaying reminders
        search_query = request.args.get('search', None)
        if search_query:
            reminders = Reminder.query.filter(Reminder.content.ilike(f"%{search_query}%")).all()
        else:
            reminders = Reminder.query.all()

        return render_template('reminder.html', reminders=reminders)
import requests
# Function to fetch currency exchange rates
def get_currency_rates(base_currency):
    api_key = 'f1b49588a1544bb39a3d46dd4728706e'  # Replace 'YOUR_API_KEY' with your actual API key
    api_url = f'https://open.er-api.com/v6/latest/{base_currency}?apikey={api_key}'

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        if response.status_code == 200:
            return data['rates']
        else:
            return None
    except Exception as e:
        print(f"Error fetching currency rates: {e}")
        return None

@app.route('/financial_forecast', methods=['GET', 'POST'])
def financial_forecast():
    if request.method == 'POST':
        selected_zone = request.form.get('zone')

        # Perform any desired action with the selected zone
        print(f"Selected Zone: {selected_zone}")

        # You can add more logic here based on your requirements

    return render_template('financial_forecast.html')

@app.route('/generate_report', methods=['POST'])
def generate_report():
    selected_zone = request.form.get('zone')

    # Add logic to generate the Power BI report based on the selected zone
    # Replace the following print statement with your actual logic
    print(f"Generating report for Zone: {selected_zone}")

    # You can redirect to another page with the selected_zone as a parameter
    return redirect(url_for('report_generated', selected_zone=selected_zone))

@app.route('/report_generated/<selected_zone>')
def report_generated(selected_zone):
    # You can perform additional logic or fetch data based on the selected_zone if needed
    # For now, let's just render the template with the selected_zone
    return render_template('report_generated.html', selected_zone=selected_zone)

@app.route('/currency_rates')
def currency_rates():
    base_currency = request.args.get('base_currency', 'INR')  # Default to USD if not provided
    rates = get_currency_rates(base_currency)
    if rates:
        return render_template('currency_rates.html', base_currency=base_currency, rates=rates)
    else:
        flash('Unable to fetch currency rates', 'error')
        return redirect(url_for('manage_expenses'))
    
@app.route('/terralogin')
def terralogin():
    return render_template('terralogin.html')

@app.route('/signupfile')
def signup():
    return render_template('signupfile.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/terratech')
def terratech():
    return render_template('terratech.html')

@app.route('/Mentorship')
def Mentorship():
    return render_template('Mentorship.html')

@app.route('/Networking')
def Networking():
    return render_template('Networking.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/startup1')
def startup1():
    return render_template('startup1.html')

@app.route('/startup2')
def startup2():
    return render_template('startup2.html')

@app.route('/jobmain')
def jobmain():
    return render_template('jobmain.html')

@app.route('/jobmainpage')
def jobmainpage():
    return render_template('jobmainpage.html')

@app.route('/jobmainpage2')
def jobmainpage2():
    return render_template('jobmainpage2.html')

@app.route('/jobposting')
def jobposting():
    return render_template('jobposting.html')

@app.route('/skilltest')
def skilltest():
    return render_template('skilltest.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # Handle form submission here
        # Access form data using request.form['input_name']
        # Process the form data as per your requirements
        return 'Form submitted successfully!'
    
df = pd.read_csv("market_.csv")

def occurrences_of_states():
    state_counts = df['State'].value_counts()
    plt.figure(figsize=(10, 6))
    state_counts.plot(kind='bar', color="red")
    plt.title('Occurrences of States in the Dataset')
    plt.xlabel('State')
    plt.ylabel('Count')
    plt.xticks(rotation=90)  
    plt.savefig('static/state_occurrences.png')  # Save the plot as an image
    return 'static/state_occurrences.png'

def crop_types_in_each_state():
    state_crop_counts = df.groupby(['State', 'CROP1 NAME']).size().unstack(fill_value=0)

    plt.figure(figsize=(15, 10))
    state_crop_counts.plot(kind='bar', stacked=True)
    plt.title('Crop Types in Each State')
    plt.xlabel('State')
    plt.ylabel('Count')
    plt.xticks(rotation=90)  
    plt.legend(title='Crop Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('static/state_crop_types.png')  # Save the plot as an image
    return 'static/state_crop_types.png'

def crop_frequencies_by_state():
    unique_states = df['State'].unique()
    num_rows = int(np.ceil(len(unique_states) / 3))
    fig, axs = plt.subplots(num_rows, 3, figsize=(15, num_rows * 4))
    axs = axs.flatten()
    for i, state in enumerate(unique_states):
        state_df = df[df['State'] == state]

        unique_crops = state_df['CROP1 NAME'].unique()

        axs[i].hist(state_df['CROP1 NAME'], bins=len(unique_crops), color='red', edgecolor='black')

        axs[i].set_xticks(range(len(unique_crops)))
        axs[i].set_xticklabels(unique_crops, rotation=45, ha='right')

        axs[i].set_title(f'Crop Frequencies in {state}')
        axs[i].set_xlabel('Crop Name')
        axs[i].set_ylabel('Frequency')
        axs[i].grid(axis='y')

    for j in range(len(unique_states), len(axs)):
        axs[j].axis('off')

    plt.tight_layout()
    plt.savefig('static/crop_frequencies_by_state.png')  # Save the plot as an image
    return 'static/crop_frequencies_by_state.png'

def plot_production_by_pincode(state_name, crop_name):
    # Filter data based on user input
    filtered_df = df[(df['State'] == state_name) & (df['CROP1 NAME'] == crop_name)]

    pincode_production = filtered_df.groupby('Pincode')['CROP1 PRODUCTION'].sum()

    if pincode_production.empty:
        print("No data found for the specified state and crop combination.")
        return None, None

    plt.figure(figsize=(10, 6))
    plt.pie(pincode_production, labels=pincode_production.index, autopct='%1.1f%%')
    plt.title(f'Production of {crop_name} by Pincode in {state_name}')
    img_path = 'static/production_by_pincode.png'
    plt.savefig(img_path)  # Save the plot as an image
    plt.close()  # Close the plot to prevent it from being displayed in the Flask app
    return img_path, pincode_production.to_dict()


def lineplot_time_series():
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x='CROP1 SEASON', y='CROP1 PRODUCTION', hue='State')
    plt.title('Time-Series of Crop Production')
    plt.xlabel('CROP1 SEASON')
    plt.ylabel('CROP1 PRODUCTION')
    plt.xticks()
    plt.legend(title='State', bbox_to_anchor=(1.05, 1), loc='upper left')
    img_path = 'static/lineplot_time_series.png'
    plt.savefig(img_path)  # Save the plot as an image
    plt.close()  # Close the plot to prevent it from being displayed in the Flask app
    return img_path

def count_plots_categorical():
    categorical_columns = ['Gender', 'State', 'ODOP product', 'CODE WORD OF PRODUCT LIST', 'CROP1 NAME', 'CROP1 SEASON']

    for col in categorical_columns:
        plt.figure(figsize=(15, 6))
        sns.countplot(data=df, x=col)
        plt.title(f'Frequency of {col}')
        plt.xlabel(col)
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        img_path = f'static/count_plot_{col}.png'
        plt.savefig(img_path)  # Save the plot as an image
        plt.close()  # Close the plot to prevent it from being displayed in the Flask app

    return [f'static/count_plot_{col}.png' for col in categorical_columns]

@app.route('/index_market')
def index_market():
    return render_template('index_market.html')


@app.route('/state_occurrences')
def state_occurrences():
    img_path = occurrences_of_states()
    return render_template('image_display.html', img_path=img_path)

@app.route('/crop_types_in_each_state')
def crop_types_in_each_state_route():
    img_path = crop_types_in_each_state()
    return render_template('image_display.html', img_path=img_path)

@app.route('/crop_frequencies_by_state')
def crop_frequencies_by_state_route():
    img_path = crop_frequencies_by_state()
    return render_template('image_display.html', img_path=img_path)

@app.route('/production_by_pincode', methods=['GET', 'POST'])
def production_by_pincode():
    if request.method == 'POST':
        state_name = request.form['state']
        crop_name = request.form['crop']
        img_path, pincode_production = plot_production_by_pincode(state_name, crop_name)
        return render_template('production_by_pincode.html', img_path=img_path, pincode_production=pincode_production)

    return render_template('production_by_pincode.html')

@app.route('/count_plots_categorical')
def count_plots_categorical_route():
    img_paths = count_plots_categorical()
    return render_template('image_display_multiple.html', img_paths=img_paths)

@app.route('/lineplot_time_series')
def lineplot_time_series_route():
    img_path = lineplot_time_series()
    return render_template('image_display.html', img_path=img_path)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

