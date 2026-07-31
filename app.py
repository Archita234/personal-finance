```python
import streamlit as st
import pandas as pd
import sqlite3
import re
import smtplib

from datetime import date, time, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Personal Finance Health System",
    page_icon="💰",
    layout="wide"
)


# ============================================================
# DATABASE
# ============================================================

DB_NAME = "finance.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # CUSTOMER TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (

            CustomerID TEXT PRIMARY KEY,

            Name TEXT NOT NULL,

            Email TEXT NOT NULL,

            OpeningBalance REAL NOT NULL,

            CurrentBalance REAL NOT NULL,

            CreatedDate TEXT NOT NULL

        )
    """)

    # --------------------------------------------------------
    # MONTHLY FINANCE TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_finance (

            ID INTEGER PRIMARY KEY AUTOINCREMENT,

            CustomerID TEXT NOT NULL,

            FinanceMonth TEXT NOT NULL,

            Income REAL NOT NULL,

            Budget REAL NOT NULL,

            RemainingBudget REAL NOT NULL,

            BudgetAdded INTEGER DEFAULT 0,

            UNIQUE(CustomerID, FinanceMonth),

            FOREIGN KEY(CustomerID)
                REFERENCES customers(CustomerID)

        )
    """)

    # --------------------------------------------------------
    # TRANSACTION TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            TransactionID TEXT PRIMARY KEY,

            CustomerID TEXT NOT NULL,

            TransactionAmount REAL NOT NULL,

            TransactionDate TEXT NOT NULL,

            TransactionTime TEXT NOT NULL,

            Category TEXT NOT NULL,

            Merchant TEXT NOT NULL,

            CustAccountBalance REAL NOT NULL,

            RemainingBudget REAL NOT NULL,

            TransactionDay TEXT NOT NULL,

            TransactionMonth TEXT NOT NULL,

            EventDate INTEGER NOT NULL,

            IsWeekend INTEGER NOT NULL,

            FOREIGN KEY(CustomerID)
                REFERENCES customers(CustomerID)

        )
    """)

    conn.commit()
    conn.close()


create_tables()


# ============================================================
# VALIDATION
# ============================================================

def valid_email(email):

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.match(pattern, email) is not None


# ============================================================
# CUSTOMER ID
# ============================================================

def generate_customer_id():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT CustomerID
        FROM customers
        ORDER BY rowid DESC
        LIMIT 1
    """)

    result = cursor.fetchone()

    conn.close()

    if result is None:
        return "CUST0001"

    last_id = result[0]

    number = int(
        last_id.replace("CUST", "")
    )

    return f"CUST{number + 1:04d}"


# ============================================================
# TRANSACTION ID
# ============================================================

def generate_transaction_id():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TransactionID
        FROM transactions
        ORDER BY rowid DESC
        LIMIT 1
    """)

    result = cursor.fetchone()

    conn.close()

    if result is None:
        return "TXN0001"

    last_id = result[0]

    number = int(
        last_id.replace("TXN", "")
    )

    return f"TXN{number + 1:04d}"


# ============================================================
# GET CUSTOMER
# ============================================================

def get_customer(customer_id):

    conn = get_connection()

    data = pd.read_sql_query(
        """
        SELECT *
        FROM customers
        WHERE CustomerID = ?
        """,
        conn,
        params=(customer_id,)
    )

    conn.close()

    return data


# ============================================================
# GET MONTH KEY
# ============================================================

def get_month_key(selected_date=None):

    if selected_date is None:
        selected_date = date.today()

    return selected_date.strftime("%Y-%m")


# ============================================================
# GET MONTHLY FINANCE
# ============================================================

def get_monthly_finance(
    customer_id,
    month_key
):

    conn = get_connection()

    data = pd.read_sql_query(
        """
        SELECT *
        FROM monthly_finance
        WHERE CustomerID = ?
        AND FinanceMonth = ?
        """,
        conn,
        params=(
            customer_id,
            month_key
        )
    )

    conn.close()

    return data


# ============================================================
# CREATE CUSTOMER
# ============================================================

def create_customer(
    name,
    email,
    opening_balance,
    income,
    budget
):

    customer_id = generate_customer_id()

    today = date.today()

    current_month = get_month_key(today)

    # --------------------------------------------------------
    # Initial balance
    #
    # Opening balance + current month's budget
    # --------------------------------------------------------

    current_balance = (
        opening_balance + budget
    )

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO customers
        (
            CustomerID,
            Name,
            Email,
            OpeningBalance,
            CurrentBalance,
            CreatedDate
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        customer_id,
        name,
        email,
        opening_balance,
        current_balance,
        today.isoformat()
    ))

    # --------------------------------------------------------
    # CURRENT MONTH FINANCE
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO monthly_finance
        (
            CustomerID,
            FinanceMonth,
            Income,
            Budget,
            RemainingBudget,
            BudgetAdded
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        customer_id,
        current_month,
        income,
        budget,
        budget,
        1
    ))

    conn.commit()
    conn.close()

    return customer_id


# ============================================================
# UPDATE MONTHLY FINANCE
# ============================================================

def update_monthly_finance(
    customer_id,
    month_key,
    income,
    budget
):

    customer = get_customer(
        customer_id
    )

    if customer.empty:
        return False, "Customer ID not found."

    if income <= 0:
        return False, "Income must be greater than ₹0."

    if budget <= 0:
        return False, "Budget must be greater than ₹0."

    if budget > income:
        return False, "Budget cannot be greater than income."

    existing = get_monthly_finance(
        customer_id,
        month_key
    )

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # NEW MONTH
    # --------------------------------------------------------

    if existing.empty:

        # Current balance before adding budget
        cursor.execute("""
            SELECT CurrentBalance
            FROM customers
            WHERE CustomerID = ?
        """, (customer_id,))

        result = cursor.fetchone()

        current_balance = float(
            result[0]
        )

        # Add new monthly budget ONCE
        new_balance = (
            current_balance + budget
        )

        cursor.execute("""
            UPDATE customers
            SET CurrentBalance = ?
            WHERE CustomerID = ?
        """, (
            new_balance,
            customer_id
        ))

        cursor.execute("""
            INSERT INTO monthly_finance
            (
                CustomerID,
                FinanceMonth,
                Income,
                Budget,
                RemainingBudget,
                BudgetAdded
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            month_key,
            income,
            budget,
            budget,
            1
        ))

        conn.commit()
        conn.close()

        return True, (
            f"Monthly information added. "
            f"₹{budget:,.2f} has been added "
            f"to your account balance."
        )

    # --------------------------------------------------------
    # EXISTING MONTH
    # --------------------------------------------------------

    else:

        old_income = float(
            existing.iloc[0]["Income"]
        )

        old_budget = float(
            existing.iloc[0]["Budget"]
        )

        old_remaining = float(
            existing.iloc[0]["RemainingBudget"]
        )

        budget_added = int(
            existing.iloc[0]["BudgetAdded"]
        )

        # ----------------------------------------------------
        # We allow updating income/budget.
        #
        # But we must NOT add the budget again if it
        # was already added to the account.
        # ----------------------------------------------------

        amount_already_spent = (
            old_budget - old_remaining
        )

        # New remaining budget
        new_remaining = max(
            budget - amount_already_spent,
            0
        )

        cursor.execute("""
            UPDATE monthly_finance
            SET Income = ?,
                Budget = ?,
                RemainingBudget = ?
            WHERE CustomerID = ?
            AND FinanceMonth = ?
        """, (
            income,
            budget,
            new_remaining,
            customer_id,
            month_key
        ))

        conn.commit()
        conn.close()

        return True, (
            "Monthly Income and Budget updated."
        )


# ============================================================
# CHECK MONTHLY UPDATE
# ============================================================

def monthly_update_required(
    customer_id
):

    current_month = get_month_key()

    monthly = get_monthly_finance(
        customer_id,
        current_month
    )

    return monthly.empty


# ============================================================
# CURRENT BALANCE
# ============================================================

def get_current_balance(
    customer_id
):

    customer = get_customer(
        customer_id
    )

    if customer.empty:
        return None

    return float(
        customer.iloc[0]["CurrentBalance"]
    )


# ============================================================
# ADD TRANSACTION
# ============================================================

def add_transaction(
    customer_id,
    amount,
    transaction_date,
    transaction_time,
    category,
    merchant
):

    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    customer = get_customer(
        customer_id
    )

    if customer.empty:

        return False, (
            "Customer ID not found."
        )

    # --------------------------------------------------------
    # MONTH
    # --------------------------------------------------------

    month_key = get_month_key(
        transaction_date
    )

    monthly = get_monthly_finance(
        customer_id,
        month_key
    )

    # --------------------------------------------------------
    # NEW MONTH RESTRICTION
    # --------------------------------------------------------

    if monthly.empty:

        return False, (
            "This month's Income and Budget "
            "have not been entered yet. "
            "Please update them first."
        )

    monthly_info = monthly.iloc[0]

    remaining_budget = float(
        monthly_info["RemainingBudget"]
    )

    # --------------------------------------------------------
    # CURRENT BALANCE
    # --------------------------------------------------------

    current_balance = get_current_balance(
        customer_id
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if amount <= 0:

        return False, (
            "Transaction amount must be "
            "greater than ₹0."
        )

    if amount > current_balance:

        return False, (
            "Insufficient account balance."
        )

    if amount > remaining_budget:

        return False, (
            "Transaction amount cannot be "
            "greater than your remaining "
            "monthly budget."
        )

    # --------------------------------------------------------
    # AUTOMATIC FIELDS
    # --------------------------------------------------------

    transaction_id = (
        generate_transaction_id()
    )

    transaction_day = (
        transaction_date.strftime("%A")
    )

    transaction_month = (
        transaction_date.strftime("%B")
    )

    event_date = transaction_date.day

    is_weekend = int(
        transaction_date.weekday() >= 5
    )

    # --------------------------------------------------------
    # UPDATE BALANCE
    # --------------------------------------------------------

    new_balance = (
        current_balance - amount
    )

    # --------------------------------------------------------
    # UPDATE REMAINING BUDGET
    # --------------------------------------------------------

    new_remaining_budget = (
        remaining_budget - amount
    )

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE customers
        SET CurrentBalance = ?
        WHERE CustomerID = ?
    """, (
        new_balance,
        customer_id
    ))

    cursor.execute("""
        UPDATE monthly_finance
        SET RemainingBudget = ?
        WHERE CustomerID = ?
        AND FinanceMonth = ?
    """, (
        new_remaining_budget,
        customer_id,
        month_key
    ))

    cursor.execute("""
        INSERT INTO transactions
        (
            TransactionID,
            CustomerID,
            TransactionAmount,
            TransactionDate,
            TransactionTime,
            Category,
            Merchant,
            CustAccountBalance,
            RemainingBudget,
            TransactionDay,
            TransactionMonth,
            EventDate,
            IsWeekend
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        transaction_id,
        customer_id,
        amount,
        transaction_date.isoformat(),
        transaction_time.strftime("%H:%M:%S"),
        category,
        merchant,
        new_balance,
        new_remaining_budget,
        transaction_day,
        transaction_month,
        event_date,
        is_weekend
    ))

    conn.commit()
    conn.close()

    return True, transaction_id


# ============================================================
# GET TRANSACTIONS
# ============================================================

def get_transactions(
    customer_id
):

    conn = get_connection()

    data = pd.read_sql_query(
        """
        SELECT *
        FROM transactions
        WHERE CustomerID = ?
        ORDER BY TransactionDate ASC,
                 TransactionTime ASC
        """,
        conn,
        params=(customer_id,)
    )

    conn.close()

    return data


# ============================================================
# ANOMALY DETECTION
# ============================================================

def detect_anomalies(
    data,
    income,
    budget
):

    if data.empty:
        return data

    data = data.copy()

    # --------------------------------------------------------
    # Monthly spending
    # --------------------------------------------------------

    data["Monthly_Spending"] = (
        data.groupby("TransactionMonth")
        ["TransactionAmount"]
        .transform("sum")
    )

    # --------------------------------------------------------
    # Savings
    # --------------------------------------------------------

    data["Savings"] = (
        income -
        data["Monthly_Spending"]
    )

    # --------------------------------------------------------
    # Investment
    # --------------------------------------------------------

    investment_data = data[
        data["Category"]
        .str.lower()
        .eq("investment")
    ]

    investment_total = (
        investment_data
        ["TransactionAmount"]
        .sum()
    )

    data["Investment"] = investment_total

    # --------------------------------------------------------
    # Convert time
    # --------------------------------------------------------

    data["ParsedTime"] = pd.to_datetime(
        data["TransactionTime"],
        format="%H:%M:%S"
    ).dt.time

    data["Is_Anomaly"] = 0

    # --------------------------------------------------------
    # ANOMALY RULES
    # --------------------------------------------------------

    for i in range(len(data)):

        transaction_time = (
            data.loc[i, "ParsedTime"]
        )

        if (

            # Transaction amount <= 0
            data.loc[
                i,
                "TransactionAmount"
            ] <= 0

            or

            # Monthly spending > budget
            data.loc[
                i,
                "Monthly_Spending"
            ] > budget

            or

            # Monthly spending > 80% income
            data.loc[
                i,
                "Monthly_Spending"
            ] > 0.8 * income

            or

            # Savings < 25% budget
            data.loc[
                i,
                "Savings"
            ] < 0.25 * budget

            or

            # Savings > 5x income
            data.loc[
                i,
                "Savings"
            ] > 5 * income

            or

            # Transaction between 12 AM and 4 AM
            (
                time(0, 0, 0)
                <= transaction_time
                <= time(4, 0, 0)
            )

            or

            # Savings < monthly spending
            data.loc[
                i,
                "Savings"
            ]
            <
            data.loc[
                i,
                "Monthly_Spending"
            ]

            or

            # Large transaction during first 7 days
            (
                data.loc[
                    i,
                    "TransactionAmount"
                ] * 0.8 > income

                and

                data.loc[
                    i,
                    "EventDate"
                ] <= 7
            )
        ):

            data.loc[
                i,
                "Is_Anomaly"
            ] = 1

    return data


# ============================================================
# HEALTH SCORE
# ============================================================

def calculate_health_score(
    data,
    income,
    budget
):

    if data.empty:

        return 0, "Critical"

    # --------------------------------------------------------
    # Total monthly spending
    # --------------------------------------------------------

    monthly_spending = (
        data["TransactionAmount"]
        .sum()
    )

    # --------------------------------------------------------
    # Savings
    # --------------------------------------------------------

    savings = (
        income -
        monthly_spending
    )

    # --------------------------------------------------------
    # Spending ratio
    # --------------------------------------------------------

    spending_ratio = (
        monthly_spending / income
        if income > 0
        else 0
    )

    score = 0

    # ========================================================
    # 1. SPENDING SCORE = 30
    # ========================================================

    if spending_ratio <= 0.60:

        score += 30

    elif spending_ratio <= 0.80:

        score += 25

    elif spending_ratio <= 1.00:

        score += 15

    else:

        score += 5

    # ========================================================
    # 2. SAVINGS SCORE = 20
    # ========================================================

    savings_ratio = (
        savings / income
        if income > 0
        else 0
    )

    if savings_ratio >= 0.30:

        score += 20

    elif savings_ratio >= 0.20:

        score += 15

    elif savings_ratio >= 0.10:

        score += 10

    elif savings_ratio >= 0:

        score += 5

    # ========================================================
    # 3. BUDGET SCORE = 15
    # ========================================================

    if monthly_spending <= budget:

        score += 15

    else:

        score += 5

    # ========================================================
    # 4. INVESTMENT SCORE = 10
    # ========================================================

    investment = data[
        data["Category"]
        .str.lower()
        .eq("investment")
    ]["TransactionAmount"].sum()

    investment_ratio = (
        investment / income
        if income > 0
        else 0
    )

    if investment_ratio >= 0.10:

        score += 10

    elif investment_ratio >= 0.05:

        score += 7

    elif investment_ratio > 0:

        score += 5

    # ========================================================
    # 5. BALANCE SCORE = 15
    # ========================================================

    balance = float(
        data.iloc[-1]
        ["CustAccountBalance"]
    )

    if monthly_spending <= 0:

        score += 15

    elif balance >= 3 * monthly_spending:

        score += 15

    elif balance >= monthly_spending:

        score += 10

    elif balance >= 0.5 * monthly_spending:

        score += 5

    # ========================================================
    # 6. BEHAVIOUR SCORE = 10
    # ========================================================

    behaviour = 10

    anomaly_count = int(
        data["Is_Anomaly"].sum()
    )

    if anomaly_count > 0:

        behaviour -= 5

    weekend_transactions = int(
        data["IsWeekend"].sum()
    )

    if weekend_transactions > 0:

        behaviour -= 2

    behaviour = max(
        behaviour,
        0
    )

    score += behaviour

    # ========================================================
    # CATEGORY
    # ========================================================

    if score >= 90:

        category = "Excellent"

    elif score >= 75:

        category = "Good"

    elif score >= 60:

        category = "Average"

    elif score >= 40:

        category = "Poor"

    else:

        category = "Critical"

    return int(score), category


# ============================================================
# MONTHLY REPORT DATA
# ============================================================

def get_monthly_report(
    customer_id,
    month_key
):

    customer = get_customer(
        customer_id
    )

    monthly = get_monthly_finance(
        customer_id,
        month_key
    )

    transactions = get_transactions(
        customer_id
    )

    if customer.empty or monthly.empty:

        return None

    month_transactions = transactions[
        transactions["TransactionDate"]
        .str.startswith(month_key)
    ].copy()

    return {
        "customer": customer.iloc[0],
        "monthly": monthly.iloc[0],
        "transactions": month_transactions
    }


# ============================================================
# EMAIL REPORT
# ============================================================

def send_email_report(
    customer_email,
    customer_name,
    report
):

    try:

        # ----------------------------------------------------
        # Read credentials from Streamlit secrets
        # ----------------------------------------------------

        sender_email = st.secrets[
            "email"
        ]["sender"]

        sender_password = st.secrets[
            "email"
        ]["password"]

        smtp_server = st.secrets[
            "email"
        ].get(
            "smtp_server",
            "smtp.gmail.com"
        )

        smtp_port = int(
            st.secrets[
                "email"
            ].get(
                "smtp_port",
                587
            )
        )

        monthly = report["monthly"]

        transactions = report[
            "transactions"
        ]

        income = float(
            monthly["Income"]
        )

        budget = float(
            monthly["Budget"]
        )

        spending = (
            transactions[
                "TransactionAmount"
            ].sum()
            if not transactions.empty
            else 0
        )

        savings = income - spending

        anomalies = 0

        if not transactions.empty:

            analyzed = detect_anomalies(
                transactions,
                income,
                budget
            )

            anomalies = int(
                analyzed["Is_Anomaly"].sum()
            )

            health_score, health_category = (
                calculate_health_score(
                    analyzed,
                    income,
                    budget
                )
            )

        else:

            health_score = 0
            health_category = "Critical"

        # ----------------------------------------------------
        # Email body
        # ----------------------------------------------------

        body = f"""
Personal Finance Health Report

Customer Name: {customer_name}

Customer ID: {report["customer"]["CustomerID"]}

Month: {monthly["FinanceMonth"]}

----------------------------------------

Income: ₹{income:,.2f}

Budget: ₹{budget:,.2f}

Total Spending: ₹{spending:,.2f}

Savings: ₹{savings:,.2f}

Remaining Budget:
₹{monthly["RemainingBudget"]:,.2f}

Current Account Balance:
₹{report["customer"]["CurrentBalance"]:,.2f}

----------------------------------------

Financial Health Score:
{health_score}/100

Health Category:
{health_category}

Anomalies Detected:
{anomalies}

----------------------------------------

This report was generated by
Personal Finance Health & Anomaly Detection System.
"""

        message = MIMEMultipart()

        message[
            "From"
        ] = sender_email

        message[
            "To"
        ] = customer_email

        message[
            "Subject"
        ] = (
            f"Personal Finance Report - "
            f"{monthly['FinanceMonth']}"
        )

        message.attach(
            MIMEText(
                body,
                "plain"
            )
        )

        # ----------------------------------------------------
        # Send
        # ----------------------------------------------------

        server = smtplib.SMTP(
            smtp_server,
            smtp_port
        )

        server.starttls()

        server.login(
            sender_email,
            sender_password
        )

        server.sendmail(
            sender_email,
            customer_email,
            message.as_string()
        )

        server.quit()

        return True, "Email sent successfully."

    except Exception as e:

        return False, str(e)


# ============================================================
# HEADER
# ============================================================

st.title(
    "💰 Personal Finance Health & Anomaly Detector"
)

st.caption(
    "Bank-style personal financial monitoring system"
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🏦 Finance System"
)

page = st.sidebar.radio(
    "Select an option",
    [
        "👤 Register Customer",
        "📅 Monthly Update",
        "💳 Add Transaction",
        "📊 Financial Dashboard",
        "🚨 Anomaly Detection",
        "📧 Email Report"
    ]
)


# ============================================================
# 1. REGISTER CUSTOMER
# ============================================================

if page == "👤 Register Customer":

    st.header(
        "👤 Register New Customer"
    )

    st.info(
        "Registration is required only once. "
        "Your Customer ID will remain permanent."
    )

    with st.form(
        "register_form"
    ):

        name = st.text_input(
            "Name *"
        )

        email = st.text_input(
            "Email *"
        )

        opening_balance = st.number_input(
            "Opening Account Balance (₹)",
            min_value=0.0,
            step=100.0
        )

        income = st.number_input(
            "Current Month Income (₹)",
            min_value=0.0,
            step=100.0
        )

        budget = st.number_input(
            "Current Month Budget (₹)",
            min_value=0.0,
            step=100.0
        )

        submitted = st.form_submit_button(
            "🏦 Register Customer",
            type="primary"
        )

    if submitted:

        errors = []

        if not name.strip():

            errors.append(
                "Name is required."
            )

        if not valid_email(
            email.strip()
        ):

            errors.append(
                "Enter a valid email."
            )

        if income <= 0:

            errors.append(
                "Income must be greater than ₹0."
            )

        if budget <= 0:

            errors.append(
                "Budget must be greater than ₹0."
            )

        if budget > income:

            errors.append(
                "Budget cannot be greater than income."
            )

        if errors:

            for error in errors:

                st.error(error)

        else:

            customer_id = create_customer(
                name.strip(),
                email.strip(),
                opening_balance,
                income,
                budget
            )

            st.success(
                "🎉 Customer registered successfully!"
            )

            st.subheader(
                "Your Permanent Customer ID"
            )

            st.code(
                customer_id
            )

            st.warning(
                "Save this Customer ID. "
                "Use the same ID for all future transactions."
            )

            st.write(
                f"**Initial Account Balance:** "
                f"₹{opening_balance + budget:,.2f}"
            )

            st.info(
                "The current month's budget has "
                "already been added to your account balance."
            )


# ============================================================
# 2. MONTHLY UPDATE
# ============================================================

elif page == "📅 Monthly Update":

    st.header(
        "📅 Monthly Income & Budget"
    )

    customer_id = st.text_input(
        "Customer ID"
    ).strip().upper()

    if customer_id:

        customer = get_customer(
            customer_id
        )

        if customer.empty:

            st.error(
                "Customer ID not found."
            )

        else:

            customer_info = (
                customer.iloc[0]
            )

            st.success(
                f"Welcome back, "
                f"{customer_info['Name']}!"
            )

            current_month = get_month_key()

            st.info(
                f"Current month: {current_month}"
            )

            existing = get_monthly_finance(
                customer_id,
                current_month
            )

            if existing.empty:

                st.warning(
                    "⚠️ Monthly Income and Budget "
                    "are required for this month."
                )

            else:

                st.success(
                    "✅ This month's Income and "
                    "Budget are already available."
                )

                current = existing.iloc[0]

                col1, col2, col3 = (
                    st.columns(3)
                )

                with col1:

                    st.metric(
                        "Income",
                        f"₹{current['Income']:,.0f}"
                    )

                with col2:

                    st.metric(
                        "Budget",
                        f"₹{current['Budget']:,.0f}"
                    )

                with col3:

                    st.metric(
                        "Remaining Budget",
                        f"₹{current['RemainingBudget']:,.0f}"
                    )

            st.divider()

            st.subheader(
                "Update Monthly Information"
            )

            with st.form(
                "monthly_form"
            ):

                income = st.number_input(
                    "Monthly Income (₹)",
                    min_value=0.0,
                    step=100.0
                )

                budget = st.number_input(
                    "Monthly Budget (₹)",
                    min_value=0.0,
                    step=100.0
                )

                submitted = st.form_submit_button(
                    "💾 Save Monthly Information",
                    type="primary"
                )

            if submitted:

                success, message = (
                    update_monthly_finance(
                        customer_id,
                        current_month,
                        income,
                        budget
                    )
                )

                if success:

                    st.success(message)

                else:

                    st.error(message)


# ============================================================
# 3. ADD TRANSACTION
# ============================================================

elif page == "💳 Add Transaction":

    st.header(
        "💳 Add Transaction"
    )

    customer_id = st.text_input(
        "Customer ID"
    ).strip().upper()

    if customer_id:

        customer = get_customer(
            customer_id
        )

        if customer.empty:

            st.error(
                "❌ Customer ID not found."
            )

        else:

            customer_info = (
                customer.iloc[0]
            )

            current_month = (
                get_month_key()
            )

            monthly = get_monthly_finance(
                customer_id,
                current_month
            )

            # ------------------------------------------------
            # MONTHLY UPDATE REQUIRED
            # ------------------------------------------------

            if monthly.empty:

                st.error(
                    "⚠️ You must update this "
                    "month's Income and Budget "
                    "before adding a transaction."
                )

                st.info(
                    "Go to '📅 Monthly Update' "
                    "first."
                )

            else:

                monthly_info = (
                    monthly.iloc[0]
                )

                col1, col2, col3 = (
                    st.columns(3)
                )

                with col1:

                    st.metric(
                        "Current Balance",
                        f"₹{customer_info['CurrentBalance']:,.2f}"
                    )

                with col2:

                    st.metric(
                        "Monthly Budget",
                        f"₹{monthly_info['Budget']:,.2f}"
                    )

                with col3:

                    st.metric(
                        "Remaining Budget",
                        f"₹{monthly_info['RemainingBudget']:,.2f}"
                    )

                st.divider()

                with st.form(
                    "transaction_form"
                ):

                    amount = st.number_input(
                        "Transaction Amount (₹) *",
                        min_value=0.01,
                        step=100.0
                    )

                    transaction_date = (
                        st.date_input(
                            "Transaction Date *",
                            value=date.today()
                        )
                    )

                    transaction_time = (
                        st.time_input(
                            "Transaction Time *",
                            value=datetime.now().time()
                        )
                    )

                    category = st.text_input(
                        "Category *",
                        placeholder=(
                            "Food / Shopping / "
                            "Transport / Investment"
                        )
                    )

                    merchant = st.text_input(
                        "Merchant *",
                        placeholder=(
                            "Amazon / Uber / Zomato"
                        )
                    )

                    submitted = st.form_submit_button(
                        "➕ Add Transaction",
                        type="primary"
                    )

                if submitted:

                    if not category.strip():

                        st.error(
                            "Category is required."
                        )

                    elif not merchant.strip():

                        st.error(
                            "Merchant is required."
                        )

                    else:

                        success, result = (
                            add_transaction(
                                customer_id,
                                amount,
                                transaction_date,
                                transaction_time,
                                category.strip(),
                                merchant.strip()
                            )
                        )

                        if success:

                            st.success(
                                "✅ Transaction added!"
                            )

                            st.write(
                                f"Transaction ID: "
                                f"**{result}**"
                            )

                            new_balance = (
                                get_current_balance(
                                    customer_id
                                )
                            )

                            updated_monthly = (
                                get_monthly_finance(
                                    customer_id,
                                    current_month
                                )
                            )

                            new_remaining = float(
                                updated_monthly.iloc[0]
                                ["RemainingBudget"]
                            )

                            col1, col2 = (
                                st.columns(2)
                            )

                            with col1:

                                st.metric(
                                    "New Account Balance",
                                    f"₹{new_balance:,.2f}"
                                )

                            with col2:

                                st.metric(
                                    "Remaining Budget",
                                    f"₹{new_remaining:,.2f}"
                                )

                        else:

                            st.error(result)


# ============================================================
# 4. FINANCIAL DASHBOARD
# ============================================================

elif page == "📊 Financial Dashboard":

    st.header(
        "📊 Financial Dashboard"
    )

    customer_id = st.text_input(
        "Customer ID"
    ).strip().upper()

    if st.button(
        "🔍 Load Dashboard",
        type="primary"
    ):

        customer = get_customer(
            customer_id
        )

        if customer.empty:

            st.error(
                "Customer ID not found."
            )

        else:

            customer_info = (
                customer.iloc[0]
            )

            transactions = (
                get_transactions(
                    customer_id
                )
            )

            current_month = (
                get_month_key()
            )

            monthly = (
                get_monthly_finance(
                    customer_id,
                    current_month
                )
            )

            st.success(
                f"Welcome, {customer_info['Name']}!"
            )

            # ------------------------------------------------
            # PROFILE
            # ------------------------------------------------

            st.subheader(
                "👤 Customer Profile"
            )

            col1, col2, col3 = (
                st.columns(3)
            )

            with col1:

                st.write(
                    f"**Customer ID:** "
                    f"{customer_id}"
                )

                st.write(
                    f"**Name:** "
                    f"{customer_info['Name']}"
                )

            with col2:

                st.write(
                    f"**Email:** "
                    f"{customer_info['Email']}"
                )

            with col3:

                st.write(
                    f"**Current Balance:** "
                    f"₹{customer_info['CurrentBalance']:,.2f}"
                )

            st.divider()

            # ------------------------------------------------
            # CURRENT MONTH
            # ------------------------------------------------

            if not monthly.empty:

                current = monthly.iloc[0]

                month_transactions = (
                    transactions[
                        transactions[
                            "TransactionDate"
                        ].str.startswith(
                            current_month
                        )
                    ].copy()
                )

                spending = (
                    month_transactions[
                        "TransactionAmount"
                    ].sum()
                    if not month_transactions.empty
                    else 0
                )

                income = float(
                    current["Income"]
                )

                budget = float(
                    current["Budget"]
                )

                savings = (
                    income - spending
                )

                analyzed = detect_anomalies(
                    month_transactions,
                    income,
                    budget
                )

                health_score, health_category = (
                    calculate_health_score(
                        analyzed,
                        income,
                        budget
                    )
                )

                st.subheader(
                    f"📅 {current_month} Summary"
                )

                col1, col2, col3, col4, col5 = (
                    st.columns(5)
                )

                with col1:

                    st.metric(
                        "Income",
                        f"₹{income:,.0f}"
                    )

                with col2:

                    st.metric(
                        "Budget",
                        f"₹{budget:,.0f}"
                    )

                with col3:

                    st.metric(
                        "Spending",
                        f"₹{spending:,.0f}"
                    )

                with col4:

                    st.metric(
                        "Savings",
                        f"₹{savings:,.0f}"
                    )

                with col5:

                    st.metric(
                        "Remaining Budget",
                        f"₹{current['RemainingBudget']:,.0f}"
                    )

                st.subheader(
                    "❤️ Financial Health"
                )

                col1, col2 = (
                    st.columns(2)
                )

                with col1:

                    st.metric(
                        "Health Score",
                        f"{health_score}/100"
                    )

                    st.progress(
                        health_score / 100
                    )

                with col2:

                    st.metric(
                        "Category",
                        health_category
                    )

            else:

                st.warning(
                    "Monthly Income and Budget "
                    "have not been entered."
                )

            # ------------------------------------------------
            # COMPLETE HISTORY
            # ------------------------------------------------

            st.divider()

            st.subheader(
                "📜 Complete Transaction History"
            )

            if transactions.empty:

                st.info(
                    "No transactions found."
                )

            else:

                display_data = transactions[
                    [
                        "TransactionID",
                        "TransactionAmount",
                        "TransactionDate",
                        "TransactionTime",
                        "Category",
                        "Merchant",
                        "CustAccountBalance",
                        "RemainingBudget",
                        "TransactionDay",
                        "TransactionMonth",
                        "IsWeekend"
                    ]
                ]

                st.dataframe(
                    display_data,
                    use_container_width=True,
                    hide_index=True
                )

            # ------------------------------------------------
            # CATEGORY CHART
            # ------------------------------------------------

            if not transactions.empty:

                st.subheader(
                    "📈 Spending by Category"
                )

                category_data = (
                    transactions
                    .groupby("Category")
                    ["TransactionAmount"]
                    .sum()
                    .sort_values(
                        ascending=False
                    )
                )

                st.bar_chart(
                    category_data
                )


# ============================================================
# 5. ANOMALY DETECTION
# ============================================================

elif page == "🚨 Anomaly Detection":

    st.header(
        "🚨 Anomaly Detection"
    )

    customer_id = st.text_input(
        "Customer ID"
    ).strip().upper()

    month_key = st.text_input(
        "Month",
        value=get_month_key(),
        placeholder="YYYY-MM"
    )

    if st.button(
        "🔍 Detect Anomalies",
        type="primary"
    ):

        customer = get_customer(
            customer_id
        )

        monthly = get_monthly_finance(
            customer_id,
            month_key
        )

        if customer.empty:

            st.error(
                "Customer ID not found."
            )

        elif monthly.empty:

            st.error(
                "Income and Budget for "
                f"{month_key} have not been entered."
            )

        else:

            transactions = (
                get_transactions(
                    customer_id
                )
            )

            month_transactions = (
                transactions[
                    transactions[
                        "TransactionDate"
                    ].str.startswith(
                        month_key
                    )
                ].copy()
            )

            income = float(
                monthly.iloc[0]["Income"]
            )

            budget = float(
                monthly.iloc[0]["Budget"]
            )

            analyzed = detect_anomalies(
                month_transactions,
                income,
                budget
            )

            if analyzed.empty:

                st.info(
                    "No transactions found "
                    "for this month."
                )

            else:

                anomalies = analyzed[
                    analyzed["Is_Anomaly"] == 1
                ]

                normal = analyzed[
                    analyzed["Is_Anomaly"] == 0
                ]

                col1, col2, col3 = (
                    st.columns(3)
                )

                with col1:

                    st.metric(
                        "Total Transactions",
                        len(analyzed)
                    )

                with col2:

                    st.metric(
                        "Normal",
                        len(normal)
                    )

                with col3:

                    st.metric(
                        "Anomalies",
                        len(anomalies)
                    )

                if anomalies.empty:

                    st.success(
                        "✅ No anomalous transactions detected."
                    )

                else:

                    st.error(
                        "⚠️ Anomalous transactions detected."
                    )

                    st.dataframe(
                        anomalies[
                            [
                                "TransactionID",
                                "TransactionAmount",
                                "TransactionDate",
                                "TransactionTime",
                                "Category",
                                "Merchant",
                                "Monthly_Spending",
                                "Savings",
                                "Is_Anomaly"
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True
                    )

                with st.expander(
                    "View Normal Transactions"
                ):

                    st.dataframe(
                        normal,
                        use_container_width=True,
                        hide_index=True
                    )


# ============================================================
# 6. EMAIL REPORT
# ============================================================

elif page == "📧 Email Report":

    st.header(
        "📧 Send Financial Report"
    )

    st.info(
        "The report will be sent to the "
        "email registered with the Customer ID."
    )

    customer_id = st.text_input(
        "Customer ID"
    ).strip().upper()

    month_key = st.text_input(
        "Report Month",
        value=get_month_key()
    )

    if st.button(
        "📧 Send Report",
        type="primary"
    ):

        report = get_monthly_report(
            customer_id,
            month_key
        )

        if report is None:

            st.error(
                "Customer or monthly financial "
                "record not found."
            )

        else:

            customer_info = (
                report["customer"]
            )

            success, message = (
                send_email_report(
                    customer_info["Email"],
                    customer_info["Name"],
                    report
                )
            )

            if success:

                st.success(
                    f"✅ {message}"
                )

            else:

                st.error(
                    "❌ Email could not be sent."
                )

                st.code(
                    message
                )

                st.info(
                    """
                    To enable email sending, create:

                    .streamlit/secrets.toml

                    and add your Gmail SMTP
                    credentials.
                    """
                )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption(
    "Personal Finance Health & Anomaly Detection"
)

st.sidebar.caption(
    "SQLite + Pandas + Streamlit"
)
```
