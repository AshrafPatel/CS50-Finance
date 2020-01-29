import os
import math
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd, resultproxy_to_dict_list

# Configure application
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Make sure API key is set
if not os.environ.get("API_KEY"):
    try:
        os.environ["API_KEY"]
    except:
        raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    user_shares = db.engine.execute("SELECT * FROM inventory WHERE inventory.users_id = ?", user_id)
    user_shares = resultproxy_to_dict_list(user_shares)
    balance = round(resultproxy_to_dict_list(db.engine.execute("SELECT cash FROM users WHERE id = ?", user_id))[0]["cash"], 2)

    displayTable = False
    holdings = 0
    grand_total = 0

    if user_shares == []:
        displayTable = False
    else:
        displayTable = True
        for share in user_shares:
            share["current_price"] = lookup(share["symbol"])["price"]
            holdings += lookup(share["symbol"])["price"] * float(share["quantity"])
            share["name"] = lookup(share["symbol"])["name"]
            temp_num = share["current_price"] * share["quantity"]
            share["holdings"] = round(float(temp_num), 2)
        holdings = round(holdings, 2)
    grand_total = round(holdings+balance, 2)
    return render_template("portfolio.html", user_shares=user_shares, show_table=displayTable, balance=balance, grand_total=grand_total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        user = db.engine.execute("SELECT * FROM users WHERE id=?", session["user_id"])
        user = resultproxy_to_dict_list(user)
        symbol = request.form.get("symbol").upper()
        shares = int(math.floor(float(request.form.get("shares"))))
        shareObj = lookup(symbol)
        user_id = user[0]["id"]
        if not shareObj:
            return apology("Share not found", 403)
        elif not shares:
            return apology("Quantity not specified", 403)
        if shares <= 0:
            return apology("Quantity is zero or negative", 403)
        purchasePrice = shareObj["price"]*float(shares)
        if float(user[0]["cash"]) < purchasePrice:
            return apology("Could not purchase, Balance is low", 403)
        else:
            balance = float(user[0]["cash"]) - purchasePrice
            db.engine.execute("INSERT INTO transactions (users_id, symbol, quantity, type, purchase_price) VALUES (?, ?, ?, ?, ?)", user_id, symbol, shares, "Bought", round(purchasePrice, 2))
            db.engine.execute("UPDATE users SET cash = ? WHERE id = ?", balance, user_id)
            row = db.engine.execute("SELECT * FROM inventory WHERE users_id=? AND symbol = ?", session["user_id"], symbol)
            row = resultproxy_to_dict_list(row)
            if row == []:
                db.engine.execute("INSERT INTO inventory (users_id, symbol, quantity) VALUES (?, ?, ?)", user_id, symbol, shares)
            else:
                quantity = int(row[0]["quantity"]) + int(shares)
                db.engine.execute("UPDATE inventory SET quantity = ? WHERE users_id=? AND symbol = ?", quantity, user_id, symbol)
            return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    user_history = db.engine.execute("SELECT * FROM transactions WHERE users_id = ?", user_id)
    user_history = resultproxy_to_dict_list(user_history)
    displayTable = False
    if user_history == []:
        displayTable = False
    else:
        displayTable = True
    return render_template("history.html", user_history=user_history, show_table=displayTable)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.engine.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        rows = resultproxy_to_dict_list(rows)

        # Ensure username exists and password is correct
        if rows == [] or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get Quote"""
    if request.method == "GET":
        return render_template("quote.html")
    else:
        share = request.form.get("symbol").upper()
        shareObj = lookup(share)
        return render_template("quoted.html", shareObj=shareObj)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register User"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        password2 = request.form.get("password2")

        row = db.engine.execute("SELECT * FROM users WHERE users.username = ?", username)
        row = resultproxy_to_dict_list(row)
        print(row)
        if not username or row != []:
            return apology("Invalid username or username may already exist", 403)
        elif password != password2 or not password or not password2:
            return apology("Invalid password, please try again", 403)
        else:
            db.engine.execute("INSERT INTO users (username, hash, cash) VALUES (?, ?, ?)", username, generate_password_hash(password), 10000)
            rows = db.engine.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
            rows = resultproxy_to_dict_list(rows)
            session["user_id"] = rows[0]["id"]
            return redirect("/")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]
    user_shares = db.engine.execute("SELECT * FROM inventory WHERE inventory.users_id = ?", user_id)
    user_shares = resultproxy_to_dict_list(user_shares)
    display_shares = False
    if request.method == "GET":
        if user_shares == []:
            display_shares = False
        else:
            display_shares = True
        return render_template("sell.html", user_shares=user_shares, display_shares=display_shares)
    else:
        form_share =  request.form.get("share")
        form_quantity = int(math.floor(float(request.form.get("quantity"))))
        shareObj = lookup(form_share)
        if not shareObj:
            return apology("Could not find symbol", 403)
        share_inventory = resultproxy_to_dict_list(db.engine.execute("SELECT * FROM inventory WHERE users_id=? AND symbol=?", user_id, form_share))[0]["quantity"]
        if not form_quantity or int(share_inventory)-int(form_quantity) < 0:
            return apology("Please specify correct quantity")
        else:
            user = db.engine.execute("SELECT * FROM users WHERE id=?", session["user_id"])
            user = resultproxy_to_dict_list(user)
            new_quantity = int(share_inventory) - int(form_quantity)
            if new_quantity == 0:
                db.engine.execute("DELETE FROM inventory WHERE users_id=? AND symbol=?", user_id, form_share)
            else:
                db.engine.execute("UPDATE inventory SET quantity = ? WHERE users_id=? AND symbol = ?", new_quantity, user_id, form_share)
            selling_price = shareObj["price"]*float(form_quantity)
            new_balance = user[0]["cash"] + selling_price
            db.engine.execute("INSERT INTO transactions (users_id, symbol, quantity, type, purchase_price) VALUES (?, ?, ?, ?, ?)", user_id, form_share, form_quantity, "Sold", round(selling_price,2))
            db.engine.execute("UPDATE users SET cash = ? WHERE id = ?", new_balance, user_id)
        return redirect("/")

@app.route("/increase", methods=["POST"])
@login_required
def increase():
    if request.method == "POST":
        user_id = session["user_id"]
        user = db.engine.execute("SELECT * FROM users WHERE id=?", session["user_id"])
        user = resultproxy_to_dict_list(user)
        symbol = request.form.get("increase")
        share_inventory = resultproxy_to_dict_list(db.engine.execute("SELECT * FROM inventory WHERE users_id=? AND symbol=?", user_id, symbol))[0]["quantity"]
        new_quantity = int(share_inventory) + 1
        shareObj = lookup(symbol)
        db.engine.execute("UPDATE inventory SET quantity = ? WHERE users_id=? AND symbol = ?", new_quantity, user_id, symbol)
        purchase_price = shareObj["price"]
        new_balance = user[0]["cash"] - purchase_price
        db.engine.execute("INSERT INTO transactions (users_id, symbol, quantity, type, purchase_price) VALUES (?, ?, ?, ?, ?)", user_id, symbol, 1, "Bought", round(purchase_price,2))
        db.engine.execute("UPDATE users SET cash = ? WHERE id = ?", new_balance, user_id)
        return redirect("/")


@app.route("/decrease", methods=["POST"])
@login_required
def decrease():
    if request.method == "POST":
        user_id = session["user_id"]
        user = db.engine.execute("SELECT * FROM users WHERE id=?", session["user_id"])
        user = resultproxy_to_dict_list(user)
        symbol = request.form.get("decrease")
        share_inventory = resultproxy_to_dict_list(db.engine.execute("SELECT * FROM inventory WHERE users_id=? AND symbol=?", user_id, symbol))[0]["quantity"]
        new_quantity = int(share_inventory) - 1
        shareObj = lookup(symbol)
        db.engine.execute("UPDATE inventory SET quantity = ? WHERE users_id=? AND symbol = ?", new_quantity, user_id, symbol)
        purchase_price = shareObj["price"]
        new_balance = user[0]["cash"] + purchase_price
        db.engine.execute("INSERT INTO transactions (users_id, symbol, quantity, type, purchase_price) VALUES (?, ?, ?, ?, ?)", user_id, symbol, 1, "Bought", round(purchase_price,2))
        db.engine.execute("UPDATE users SET cash = ? WHERE id = ?", new_balance, user_id)
        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)