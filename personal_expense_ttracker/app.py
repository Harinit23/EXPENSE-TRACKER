from flask import Flask, render_template, request, redirect, session, g
import sqlite3

app = Flask(__name__)
app.secret_key = 'a'
app.config['DATABASE'] = 'expenses.db'

# Database functions
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Routes

@app.route("/home")
def home():
    return render_template("homepage.html")

@app.route("/")
def add():
    return render_template("home.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM register WHERE username = ?', (username,))
        account = cursor.fetchone()

        if account:
            msg = 'Account already exists!'
        else:
            cursor.execute('INSERT INTO register VALUES (NULL, ?, ?, ?)', (username, email, password))
            get_db().commit()
            msg = 'You have successfully registered!'
            return render_template('signup.html', msg=msg)

    return render_template('signup.html', msg=msg)

@app.route("/signin")
def signin():
    return render_template("login.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    global userid
    msg = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM register WHERE username = ? AND password = ?', (username, password), )
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            userid = account[0]
            session['username'] = account[1]

            return redirect('/home')
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg=msg)

@app.route("/add")
def adding():
    return render_template('add.html')

@app.route('/addexpense', methods=['GET', 'POST'])
def addexpense():
    date = request.form['date']
    expensename = request.form['expensename']
    amount = request.form['amount']
    paymode = request.form['paymode']
    category = request.form['category']

    cursor = get_db().cursor()
    cursor.execute('INSERT INTO expenses VALUES (NULL,  ?, ?, ?, ?, ?, ?)',
                   (session['id'], date, expensename, amount, paymode, category))
    get_db().commit()
    print(date + " " + expensename + " " + amount + " " + paymode + " " + category)

    return redirect("/display")

@app.route("/display")
def display():
    print(session["username"], session['id'])

    cursor = get_db().cursor()
    cursor.execute('SELECT * FROM expenses WHERE userid = ? ORDER BY `expenses`.`date` DESC',
                   (str(session['id']),))
    expense = cursor.fetchall()

    return render_template('display.html', expense=expense)

@app.route('/delete/<string:id>', methods=['POST', 'GET'])
def delete(id):
    cursor = get_db().cursor()
    cursor.execute('DELETE FROM expenses WHERE  id = ?', (id,))
    get_db().commit()
    print('Deleted successfully')
    return redirect("/display")

@app.route('/edit/<id>', methods=['POST', 'GET'])
def edit(id):
    cursor = get_db().cursor()
    cursor.execute('SELECT * FROM expenses WHERE  id = ?', (id,))
    row = cursor.fetchall()
    print(row[0])
    return render_template('edit.html', expenses=row[0])

@app.route('/update/<id>', methods=['POST'])
def update(id):
    if request.method == 'POST':
        date = request.form['date']
        expensename = request.form['expensename']
        amount = request.form['amount']
        paymode = request.form['paymode']
        category = request.form['category']

        cursor = get_db().cursor()
        cursor.execute("UPDATE `expenses` SET `date` = ?, `expensename` = ?, `amount` = ?, `paymode` = ?, "
                       "`category` = ? WHERE `expenses`.`id` = ? ", (date, expensename, amount, str(paymode),
                                                                    str(category), id))
        get_db().commit()
        return redirect("/display")

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return render_template('home.html')

# New Routes

@app.route("/today")
def today():
    cursor = get_db().cursor()
    cursor.execute('SELECT TIME(date)   , amount FROM expenses  WHERE userid = ? AND DATE(date) = DATE("now") ',
                   (str(session['id']),))
    texpense = cursor.fetchall()

    cursor = get_db().cursor()
    cursor.execute('SELECT * FROM expenses WHERE userid = ? AND DATE(date) = DATE("now") ORDER BY '
                   '`expenses`.`date` DESC', (str(session['id']),))
    expense = cursor.fetchall()

    total = 0
    t_food = 0
    t_entertainment = 0
    t_business = 0
    t_rent = 0
    t_EMI = 0
    t_other = 0

    for x in expense:
        total += x[4]
        if x[6] == "food":
            t_food += x[4]
        elif x[6] == "entertainment":
            t_entertainment += x[4]
        elif x[6] == "business":
            t_business += x[4]
        elif x[6] == "rent":
            t_rent += x[4]
        elif x[6] == "EMI":
            t_EMI += x[4]
        elif x[6] == "other":
            t_other += x[4]

    return render_template("today.html", texpense=texpense, expense=expense, total=total,
                           t_food=t_food, t_entertainment=t_entertainment,
                           t_business=t_business, t_rent=t_rent,
                           t_EMI=t_EMI, t_other=t_other)

@app.route("/month")
def month():
    cursor = get_db().cursor()
    cursor.execute(
        'SELECT strftime("%Y-%m", date) AS month, SUM(amount) '
        'FROM expenses WHERE userid= ? AND strftime("%Y-%m", date) = strftime("%Y-%m", "now") '
        'GROUP BY month ORDER BY month ', (str(session['id']),))
    texpense = cursor.fetchall()

    cursor = get_db().cursor()
    cursor.execute(
        'SELECT * FROM expenses WHERE userid= ? AND strftime("%Y-%m", date) = strftime("%Y-%m", "now") '
        'ORDER BY `expenses`.`date` DESC',
        (str(session['id']),))
    expense = cursor.fetchall()

    total = 0
    t_food = 0
    t_entertainment = 0
    t_business = 0
    t_rent = 0
    t_EMI = 0
    t_other = 0

    for x in expense:
        total += x[4]
        if x[6] == "food":
            t_food += x[4]
        elif x[6] == "entertainment":
            t_entertainment += x[4]
        elif x[6] == "business":
            t_business += x[4]
        elif x[6] == "rent":
            t_rent += x[4]
        elif x[6] == "EMI":
            t_EMI += x[4]
        elif x[6] == "other":
            t_other += x[4]

    return render_template("month.html", texpense=texpense, expense=expense, total=total,
                           t_food=t_food, t_entertainment=t_entertainment,
                           t_business=t_business, t_rent=t_rent,
                           t_EMI=t_EMI, t_other=t_other)

@app.route("/year")
def year():
    cursor = get_db().cursor()
    cursor.execute(
        'SELECT strftime("%Y", date) AS year, SUM(amount) '
        'FROM expenses WHERE userid= ? AND strftime("%Y", date) = strftime("%Y", "now") '
        'GROUP BY year ORDER BY year ', (str(session['id']),))
    texpense = cursor.fetchall()

    cursor = get_db().cursor()
    cursor.execute(
        'SELECT * FROM expenses WHERE userid= ? AND strftime("%Y", date) = strftime("%Y", "now") '
        'ORDER BY `expenses`.`date` DESC',
        (str(session['id']),))
    expense = cursor.fetchall()

    total = 0
    t_food = 0
    t_entertainment = 0
    t_business = 0
    t_rent = 0
    t_EMI = 0
    t_other = 0

    for x in expense:
        total += x[4]
        if x[6] == "food":
            t_food += x[4]
        elif x[6] == "entertainment":
            t_entertainment += x[4]
        elif x[6] == "business":
            t_business += x[4]
        elif x[6] == "rent":
            t_rent += x[4]
        elif x[6] == "EMI":
            t_EMI += x[4]
        elif x[6] == "other":
            t_other += x[4]

    return render_template("year.html", texpense=texpense, expense=expense, total=total,
                           t_food=t_food, t_entertainment=t_entertainment,
                           t_business=t_business, t_rent=t_rent,
                           t_EMI=t_EMI, t_other=t_other)

@app.route("/now")
def now():
    cursor = get_db().cursor()
    cursor.execute(
        'SELECT DATE(date)   , SUM(amount) '
        'FROM expenses WHERE userid= ? AND DATE(date) = DATE("now") '
        'GROUP BY DATE(date) ORDER BY DATE(date) DESC', (str(session['id']),))
    texpense = cursor.fetchall()

    cursor = get_db().cursor()
    cursor.execute(
        'SELECT * FROM expenses WHERE userid= ? AND DATE(date) = DATE("now") '
        'ORDER BY `expenses`.`date` DESC',
        (str(session['id']),))
    expense = cursor.fetchall()

    total = 0
    t_food = 0
    t_entertainment = 0
    t_business = 0
    t_rent = 0
    t_EMI = 0
    t_other = 0

    for x in expense:
        total += x[4]
        if x[6] == "food":
            t_food += x[4]
        elif x[6] == "entertainment":
            t_entertainment += x[4]
        elif x[6] == "business":
            t_business += x[4]
        elif x[6] == "rent":
            t_rent += x[4]
        elif x[6] == "EMI":
            t_EMI += x[4]
        elif x[6] == "other":
            t_other += x[4]

    return render_template("now.html", texpense=texpense, expense=expense, total=total,
                           t_food=t_food, t_entertainment=t_entertainment,
                           t_business=t_business, t_rent=t_rent,
                           t_EMI=t_EMI, t_other=t_other)

@app.route("/limit")
def limit():
    return redirect('/limitn')

@app.route("/limitnum", methods=['POST'])
def limitnum():
    if request.method == "POST":
        number = request.form['number']
        cursor = get_db().cursor()
        cursor.execute('INSERT INTO limits VALUES (NULL, ?, ?) ', (session['id'], number))
        get_db().commit()
        return redirect('/limitn')

@app.route("/limitn")
def limitn():
    cursor = get_db().cursor()
    cursor.execute('SELECT limitss FROM `limits` ORDER BY `limits`.`id` DESC LIMIT 1')
    x = cursor.fetchone()
    s = x[0]
    return render_template("limit.html", y=s)

if __name__ == "__main__":
    app.run(debug=True)
