from flask import Flask, request, flash, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text, func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stocks.sqlite3'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)

class stocks(db.Model):
    id = db.Column('stock_id', db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True)  # Indexed for filtering
    price = db.Column(db.Float)
    industry = db.Column(db.String(200), index=True)  # Added index
    div = db.Column(db.Float)

    def __init__(self, name, price, industry, div, id=None):
        self.id = id
        self.name = name
        self.price = price
        self.industry = industry
        self.div = div

@app.route('/', methods=['GET', 'POST'])
def show_all():
    conn = db.engine.connect()
    stmt = text("SELECT * FROM stocks WHERE 1=1")
    params = {}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        industry = request.form.get('industry', '').strip()

        if name:
            stmt = text("SELECT * FROM stocks WHERE name LIKE :name")
            params['name'] = f"%{name}%"
        if industry:
            if 'name' in params:
                stmt = text("SELECT * FROM stocks WHERE name LIKE :name AND industry LIKE :industry")
            else:
                stmt = text("SELECT * FROM stocks WHERE industry LIKE :industry")
            params['industry'] = f"%{industry}%"

    result = conn.execute(stmt, params)
    filtered_stocks = [
        stocks(row[1], row[2], row[3], row[4], row[0]) for row in result
    ]
    # Calculate statistics
    avg_price = db.session.query(func.avg(stocks.price)).scalar()
    return render_template('index.html', stocks=filtered_stocks, avg_price=avg_price)

@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        if not request.form['name'] or not request.form['price'] or not request.form['industry']:
            flash('Please enter all the fields', 'error')
        else:
            stock = stocks(request.form['name'], float(request.form['price']),
                           request.form['industry'], float(request.form['div']))
            db.session.add(stock)
            db.session.commit()
            flash('Record was successfully added')
            return redirect(url_for('show_all'))
    return render_template('new.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    stock = stocks.query.get(id)
    if request.method == 'POST':
        if not request.form['name'] or not request.form['price'] or not request.form['industry']:
            flash('Please enter all the fields', 'error')
        else:
            stock.name = request.form['name']
            stock.price = float(request.form['price'])
            stock.industry = request.form['industry']
            stock.div = float(request.form['div'])
            db.session.commit()
            return redirect(url_for('show_all'))
    return render_template('edit.html', stock=stock)

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    stock = stocks.query.get(id)
    if stock:
        db.session.delete(stock)
        db.session.commit()
        flash('Record was successfully deleted')
    return redirect(url_for('show_all'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
