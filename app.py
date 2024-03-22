import json
import os
import re
import secrets
from datetime import date as dt_date
from datetime import datetime

import numpy as np
import pandas as pd
import plotly
import plotly.graph_objs as go
import requests
import yfinance as yf
from alpha_vantage.fundamentaldata import FundamentalData
from cs50 import SQL
from dateutil.relativedelta import relativedelta
from flask import (Flask, flash, redirect,  # Import Flask and render_template
                   render_template, request, session, url_for)
from stocknews import StockNews
from twilio.base.exceptions import TwilioException
from twilio.rest import Client
from werkzeug.security import check_password_hash, generate_password_hash

from flask_session import Session
from helpers import apology, login_required, lookup, usd

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
# Configure app to use the twilio api for OTP
app.secret_key = secrets.token_urlsafe(32)
app.config['TWILIO_SID'] = 'AC8c3d87cbe50f6db1f55d959f9f94197e'
app.config['TWILIO_AUTH_TOKEN'] = '9f27ed3860a0c8ae140645ca3c436f3b'
app.config['VERIFY_SID'] = 'VAb037b7729f50b48508eda4d053703800'
app.config['TWILIO_PHONE_NUMBER'] = '+917755910420'
app.config['messaging_service_sid'] = 'MG9752274e9e519418a7406176694466fa'

client = Client(app.config['TWILIO_SID'], app.config['TWILIO_AUTH_TOKEN'])


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


def send_otp_via_sms(to, channel="sms"):
    try:
        verification = client.verify.v2.services(app.config['VERIFY_SID']) \
            .verifications \
            .create(to=to, channel=channel)
        return verification.status
    except Exception as e:
        return f"Error sending OTP: {str(e)}"


def verify_otp(phone_number, user_provided_otp):
    try:
        print(phone_number, user_provided_otp)
        verification_check = client.verify.v2.services(app.config['VERIFY_SID']) \
            .verification_checks \
            .create(to=phone_number, code=user_provided_otp)
        
        return True, verification_check.status
    except TwilioException as e:
        return False, f"Twilio Error: {str(e)}"
    except Exception as e:
        return False, f"Error verifying OTP: {str(e)}"



@app.route("/verify_otp_registration", methods=["POST"])
def verify_otp_registration():
    phone_number = request.form.get("phone_number")
    user_provided_otp = request.form.get("otp")
    
    print(f"\n\nVerifying OTP for {phone_number} with code {user_provided_otp}\n\n")
    print(phone_number)
    
    # Verify OTP
    success, status = verify_otp(phone_number, user_provided_otp)
    print(success)
    print(status)

    if success:
        # OTP verification successful, continue with registration
        # Retrieve other form fields and proceed with user registration
         # Check if username already taken, return an apology
        check = db.execute("SELECT * FROM users WHERE username = ?;", session.get("username"))
        if len(check) != 0:
            return apology("Username already taken")
        else:
            # Generate a hash of the password
            newhash = generate_password_hash(session.get("password"))
            NewUser = session.get("username")
            NewEmail = session.get("email")
            NewPhone = session.get("phone")
            # Insert the data in the database
            try:
                db.execute("INSERT INTO users (username, hash, email, phone_no) VALUES (?, ?, ?, ?);", NewUser, newhash, NewEmail, NewPhone)
                print("User registered successfully")
                return render_template("login.html")
            except Exception as e:
                print(f"Error inserting into database: {e}")
                return apology("Error during registration")
    else:
        # OTP verification failed
        flash(f"OTP verification failed. Status: {status}", "error")
        return render_template("verify_otp_registration.html", phone_number=phone_number)



@app.route("/verify_otp_route", methods=["GET","POST"])
def verify_otp_route():
    phone_no = session.get("phone")

    if request.method == "POST":
        otp = request.form.get("otp")
        success, status = verify_otp(phone_no, otp)

        if success:
            flash(f"Approved")
            return render_template("login.html")
        else:
            flash(f"Failed: {status}")
            return render_template("verify_otp.html", phone_number=phone_no)

    return render_template('verify_otp.html', phone_number=phone_no)



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        # Check if username, email, password, confirmation, and phone were submitted
        if not request.form.get("username"):
            return apology("Must provide username")
        elif not request.form.get("email"):
            return apology("Must provide email")
        elif not request.form.get("password"):
            return apology("Must provide password")
        elif not request.form.get("confirmation"):
            return apology("Must confirm password")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match")
        elif not request.form.get("phone"):
            return apology("Must provide phone number")

        # Add email and phone number validation
        # For Email
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if not re.fullmatch(regex, request.form.get("email")):
            return apology("Enter a valid email")
        # For Phone number
        phone_regex = r"(\+\d{1,3})?\s?\(?\d{1,4}\)?[\s.-]?\d{3}[\s.-]?\d{4}"
        if not re.fullmatch(phone_regex, request.form.get("phone")):
            return apology("Enter a valid phone number")
        
        session["username"] = request.form.get("username")
        session["password"] = request.form.get("password")
        session["email"] = request.form.get("email")
        session["phone"] = request.form.get("phone")
        # Send OTP via SMS
        if send_otp_via_sms(request.form.get("phone")) != 0:
            print(f"Error sending OTP for {request.form.get('phone')}")
            return render_template("verify_otp_registration.html", phone_number=request.form.get("phone"))


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


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    if request.method == "POST":
        amount = float(request.form.get("amount"))

        # Ensure a positive amount is provided
        if amount <= 0:
            return apology("Please provide a valid amount to add", 400)

        user_id = session["user_id"]
        # Update the user's cash in the database
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?;", amount, user_id)

        flash(f"Added {usd(amount)} to your account.")
        return redirect("/")

    elif request.method == "GET":
        return render_template("add_cash.html")


@app.route("/withdraw_cash", methods=["GET","POST"])
@login_required
def withdraw_cash():
    if request.method == "POST":
        amount = float(request.form.get("amount"))
        
        current_cash = db.execute("SELECT cash FROM users WHERE id = ?;",session["user_id"])
        
        current_cash_value = float(current_cash[0]["cash"])
        
        if amount > current_cash_value:
            return apology("Insufficient funds for withdrawal.", 402)
        
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?;",amount,session["user_id"])
        
        flash(f"Withdraw {usd(amount)} from your account")
        return redirect("/")
    
    elif request.method == "GET":
        return render_template("withdraw_cash.html")
        
    
@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "POST":
        # Handle the form submission to search for a stock symbol
        company_name = request.form.get("search")
        
        if not company_name:
            flash("Please enter a company name to search.", "warning")
            return redirect(url_for("search"))

        # Make a request to Alpha Vantage API for symbol search
        api_key = "29V7B9PCLN9Q2RMD"
        search_url = f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={company_name}&apikey={api_key}'
        search_response = requests.get(search_url)
        search_results = search_response.json()

        # Extract the stock symbol from the search results
        if 'bestMatches' in search_results:
            symbol = search_results['bestMatches'][0].get('1. symbol', None)

            flash(f"{company_name} ticker symbol is {symbol}")
            return redirect(url_for("index"))


@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if request.method == "POST":
        # Handle the form submission to search for a stock symbol
        company_name = request.form.get("company")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        
        if not company_name:
            flash("Please enter a company name to search.", "warning")
            return redirect(url_for("report"))
        if not start_date:
            flash("Please enter a Start date.", "warning")
            return redirect(url_for("report"))
        if not end_date:
            flash("Please enter a End date.", "warning")
            return redirect(url_for("report"))

        # Make a request to Alpha Vantage API for symbol search
        api_key = "29V7B9PCLN9Q2RMD"
        search_url = f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={company_name}&apikey={api_key}'
        search_response = requests.get(search_url)
        search_results = search_response.json()
        # Extract the stock symbol from the search results
        if 'bestMatches' in search_results:
            ticker = search_results['bestMatches'][0].get('1. symbol', None)
            data = yf.download(ticker,start=start_date,end=end_date)
            
           #Create Plotly figure
            fig = go.Figure(data = [go.Candlestick(
                    x = data.index,
                    open = data['Open'],
                    high = data['High'],
                    low = data['Low'],
                    close = data['Close']
                )])
             # Customize layout
            fig.update_layout(
                title = 'Candlestick Chart',
                title_font = dict(color='white'),
                height = 600,  # Set the height of the chart
                width = 800,   # Set the width of the chart
                xaxis = dict(
                    title ='Date',
                    title_font = dict(color='white'),
                    tickfont = dict(color='white')
                ),
                yaxis = dict(
                    title ='Price',
                    title_font = dict(color='white'),
                    tickfont = dict(color='white')
                ),
                margin = dict(t=60, b=55, l=55, r=0),
                plot_bgcolor ='#1f2937',  #plot background color
                paper_bgcolor ='#1f2937'  #paper background color
            )
            data2 = data
            data2['% Change'] = data['Adj Close'] / data['Adj Close'].shift(1) -1
            data2.dropna(inplace = True)
            rounded_data = data2[['Open', 'High', 'Low', 'Close', 'Adj Close','Volume']].round(2)
            rounded_data['% Change'] = data2[['% Change']].round(5)
            rounded_data['Date'] = data2.index.strftime('%Y-%m-%d')
             # Annual Return
            annual_return = data2['% Change'].mean()*252*100
            # Standard deviation
            std_dev = np.std(data2['% Change'])*np.sqrt(252)
            # Risk adjust Return
            risk_adj_ret = (annual_return)/(std_dev*100)
            
            #Fundmental Data
            #Balance Sheet Information
            fd = FundamentalData(api_key,output_format='pandas')
            balance_sheet = fd.get_balance_sheet_annual(ticker)[0]
            bs = balance_sheet.T[2:]
            bs.columns = list(balance_sheet.T.iloc[0])
            print("\nBALANCE SHEET\n")
            
            #Income Statement Information
            income_statement = fd.get_income_statement_annual(ticker)[0]
            is1 = income_statement.T[2:]
            is1.columns = list(income_statement.T.iloc[0])
            print("\nINCOME STATEMENT\n")
    
            #Cash Flow Statement Information
            cash_flow = fd.get_cash_flow_annual(ticker)[0]
            cf = cash_flow.T[2:]
            cf.columns = list(cash_flow.T.iloc[0])
            print("\nCASH-FLOW STATEMENT\n")

            
            # Stock News 
            sn = StockNews(ticker,save_news=False)
            df_news = sn.read_rss()
            
            table_data_list = rounded_data.to_dict(orient='records')
            graphJSON = fig.to_json()
            # Pass fig to template
            return render_template("report_result.html", 
                                   fig=graphJSON, 
                                   tableData=table_data_list, 
                                   annual_return=annual_return, 
                                   std_dev=std_dev, 
                                   risk_adj_ret=risk_adj_ret, 
                                   balance_sheet=bs, 
                                   Income_sheet=is1,
                                    cash_flow=cf,
                                    df_news=df_news)

    elif request.method == "GET":
        return render_template("report.html")

if __name__ == "__main__":
    app.run(debug=True)
