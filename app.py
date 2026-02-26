import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Category, Transaction, Budget
from datetime import datetime
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()
    # Add some default categories if none exist
    if not Category.query.first():
        pass # Will add during registration or first login for demo

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'warning')
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            # Add default categories for the new user
            defaults = [
                ('Salary', 'income'), ('Freelance', 'income'),
                ('Food', 'expense'), ('Rent', 'expense'), 
                ('Transport', 'expense'), ('Entertainment', 'expense'),
                ('Utilities', 'expense'), ('Shopping', 'expense')
            ]
            for name, type in defaults:
                cat = Category(name=name, type=type, user_id=new_user.id)
                db.session.add(cat)
            db.session.commit()
            
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Summary data
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(5).all()
    
    # Calculate totals for this month
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    
    income_total = db.session.query(func.sum(Transaction.amount)).join(Category).filter(
        Transaction.user_id == current_user.id,
        Category.type == 'income',
        Transaction.date >= month_start
    ).scalar() or 0
    
    expense_total = db.session.query(func.sum(Transaction.amount)).join(Category).filter(
        Transaction.user_id == current_user.id,
        Category.type == 'expense',
        Transaction.date >= month_start
    ).scalar() or 0
    
    balance = income_total - expense_total
    
    # Budget alerts
    budgets = Budget.query.filter_by(user_id=current_user.id, month=now.month, year=now.year).all()
    alerts = []
    for b in budgets:
        spending = b.current_spending
        if spending >= b.amount * 0.9: # 90% or more
            alerts.append({
                'category': b.category.name,
                'spent': spending,
                'limit': b.amount,
                'percent': round((spending/b.amount)*100, 1)
            })

    return render_template('dashboard.html', 
                          income=income_total, 
                          expense=expense_total, 
                          balance=balance,
                          recent_transactions=transactions,
                          alerts=alerts)

@app.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        category_id = int(request.form.get('category_id'))
        description = request.form.get('description')
        date_str = request.form.get('date')
        date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
        
        new_tx = Transaction(amount=amount, category_id=category_id, 
                            description=description, date=date, user_id=current_user.id)
        db.session.add(new_tx)
        db.session.commit()
        flash('Transaction added!', 'success')
        return redirect(url_for('transactions'))
        
    all_tx = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('transactions.html', transactions=all_tx, categories=categories, today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/delete-transaction/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    tx = Transaction.query.get_or_404(id)
    # Security check: ensure user owns the transaction
    if tx.user_id != current_user.id:
        flash('Unauthorized action', 'error')
        return redirect(url_for('transactions'))
        
    db.session.delete(tx)
    db.session.commit()
    flash('Transaction deleted successfully', 'success')
    return redirect(url_for('transactions'))

@app.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    now = datetime.now()
    if request.method == 'POST':
        category_id = int(request.form.get('category_id'))
        amount = float(request.form.get('amount'))
        
        # Check if budget already exists for this category/month
        existing = Budget.query.filter_by(user_id=current_user.id, 
                                        category_id=category_id, 
                                        month=now.month, year=now.year).first()
        if existing:
            existing.amount = amount
        else:
            new_budget = Budget(category_id=category_id, amount=amount, 
                               month=now.month, year=now.year, user_id=current_user.id)
            db.session.add(new_budget)
        db.session.commit()
        flash('Budget set!', 'success')
        
    all_budgets = Budget.query.filter_by(user_id=current_user.id, month=now.month, year=now.year).all()
    expense_categories = Category.query.filter_by(user_id=current_user.id, type='expense').all()
    return render_template('budgets.html', budgets=all_budgets, categories=expense_categories, now=now)

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    if request.method == 'POST':
        name = request.form.get('name')
        type = request.form.get('type')
        if not name or not type:
            flash('All fields are required', 'warning')
        else:
            new_cat = Category(name=name, type=type, user_id=current_user.id)
            db.session.add(new_cat)
            db.session.commit()
            flash('Category added!', 'success')
            return redirect(url_for('categories'))
            
    user_categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories.html', categories=user_categories)

@app.route('/delete-category/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    if cat.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('categories'))
    
    # Check if category is used in transactions
    if Transaction.query.filter_by(category_id=id).first():
        flash('Cannot delete category that has transactions. Remove the transactions first.', 'warning')
        return redirect(url_for('categories'))
        
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted', 'success')
    return redirect(url_for('categories'))

@app.route('/api/chart-data')
@login_required
def chart_data():
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    
    # Expenses by category for current month
    expenses = db.session.query(Category.name, func.sum(Transaction.amount)).join(Transaction).filter(
        Transaction.user_id == current_user.id,
        Category.type == 'expense',
        Transaction.date >= month_start
    ).group_by(Category.name).all()
    
    labels = [e[0] for e in expenses]
    data = [e[1] for e in expenses]
    
    return jsonify({'labels': labels, 'values': data})

if __name__ == '__main__':
    app.run(debug=True)
