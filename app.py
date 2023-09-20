import os
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

import plotly.graph_objs as go
import numpy as np
from datetime import datetime
from datetime import date as dt_date
from flask import Flask, render_template  # Import Flask and render_template
import yfinance as yf
from dateutil.relativedelta import relativedelta 

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    stock_data = db.execute(
        "SELECT symbol, SUM(shares) AS total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
        user_id=session["user_id"])

    user_id = session["user_id"]
    cash = db.execute("SELECT cash FROM users WHERE id = ?",
                      user_id)[0]["cash"]

    total_value = cash
    grand_total = cash

    for data in stock_data:
        qoute = lookup(data["symbol"])
        data["name"] = qoute["name"]
        data["price"] = qoute["price"]
        data["value"] = data["price"] * data["total_shares"]
        total_value += data["value"]
        grand_total += data["value"]

    return render_template("index.html",
                           stock_data=stock_data, cash=cash, total_value=total_value, grand_total=grand_total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")

        if not symbol:
            return apology("must povide symbol")
        elif not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("must provide  position number of shares")

        check = lookup(symbol)
        if check is None:
            return apology("stock not exist")

        user_id = session["user_id"]

        price = check["price"]
        total_cost = int(shares) * price
        cash = db.execute("SELECT cash FROM users WHERE id = ?",
                          user_id)[0]["cash"]

        if cash < total_cost:
            return apology("not enough cash")

        # update users table
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?;", total_cost, user_id)

        #add the purchase to the history table
        db.execute("INSERT INTO transactions (user_id, symbol, shares ,price) VALUES(?, ?, ?, ?)", user_id, symbol, shares, price)

        flash(f"Bought {shares} shares of {symbol} for {usd(total_cost)}")
        return redirect("/")

    elif request.method == "GET":
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    stock_data = db.execute(
        "SELECT symbol, shares, price, timestamp FROM transactions WHERE user_id = ? ORDER BY timestamp DESC",
        user_id)

    return render_template("history.html", stock_data=stock_data)


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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
    """Get stock quote."""

    if request.method == "POST":

        # check if symbol is Enter
        if not request.form.get("symbol"):
            return apology("Enter symbol")

        quoted = lookup(request.form.get("symbol").upper())

        if quoted != None:
            return render_template("quoted.html", quote=quoted)
        else:
            return apology("stocks does not exit")

    elif request.method == "GET":
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Check if username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # check id password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        elif not request.form.get("confirmation"):
            return apology("must confirm password")

        # check if both the password match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password do not match")

        # check if username already taken, return an apology
        check = db.execute("SELECT * FROM users WHERE username = ?;", request.form.get("username"))
        if len(check) != 0:
            return apology("username Already taken")
        else:
            # Generate a hash of the password
            newhash = generate_password_hash(request.form.get("password"))
            NewUser = request.form.get("username")
            # Insert the data in the database
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?);", NewUser, newhash)

        return render_template("login.html")

    elif request.method == "GET":
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    stock_data = db.execute( 
        "SELECT symbol, SUM(shares) AS total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
        user_id=session["user_id"])

    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")

        if not symbol:
            return apology("must povide symbol")
        elif not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("must provide  position number of shares")
        else:
            shares = int(shares)

        check = lookup(symbol)
        if check is None:
            return apology("stock not exist")

        for data in stock_data:
            if data["symbol"] == symbol:
                if int(data["total_shares"]) < int(shares):
                    return apology("not enough shares")
                else:
                    price = check["price"]
                    total_sale = shares * price

                    user_id = session["user_id"]
                    db.execute("UPDATE users SET cash = cash + ? WHERE id = ?;", total_sale,user_id)
                    # ADD sale to transaction table
                    db.execute(
                        "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?);",
                        user_id, symbol, -shares, price)

                    flash(f"sold {shares} shares of {symbol} for {usd(total_sale)} ")
                    return redirect("/")
        return apology("symbol not found")

    else:
        return render_template("sell.html", stock_data=stock_data)


# ... (import statements and Flask app setup)
 
 
 

@app.route("/chart", methods=["POST", "GET"])
@login_required
def chart():
    user_stocks = db.execute("SELECT symbol, SUM(shares) AS total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id=session["user_id"])

    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        
        x = []
        y = []
        ma = []

        def moving_average(interval, window_size):
            window = np.ones(int(window_size)) / float(window_size)
            return np.convolve(interval, window, 'same')

            
        # Calculate the end date as the current date
        end_date = dt_date.today()
        
        # Calculate the start date as 10 years before the end date
        start_date = end_date - relativedelta(years=10)

        # Fetch historical data using yfinance
        data = yf.download(symbol, start=start_date, end=end_date)

        if data.empty:
            print("Couldn't connect to Yahoo Finance or no data available.")
        else:
            x = data.index.strftime('%Y-%m-%d').tolist()
            y = data['Close'].tolist()
            
            # Convert the NumPy ndarray to a list
            ma = moving_average(y, 10).tolist()

            xy_data = {
                "x": x,
                "y": y,
                "mode": "markers",
                "marker": {"size": 4},
                "name": symbol
            }
            mov_avg = {
                "x": x[5:-4],
                "y": ma[5:-4],
                "type": "scatter",
                "mode": "lines",
                "line": {"width": 2, "color": "red"},
                "name": "Moving average"
            }
            chart_data = [xy_data, mov_avg]
            
            return render_template('charts.html', chart_data=chart_data)

    elif request.method == "GET":
        return render_template('chart.html',user_stocks=user_stocks)