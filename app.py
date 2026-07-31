import streamlit as st
import pandas as pd
import uuid
from datetime import datetime


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Personal Finance Analyzer",
    page_icon="💰",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("💰 Personal Finance Health Analyzer")

st.write(
    "Enter your personal and transaction information below. "
    "Required fields must be completed before the transaction "
    "can be added."
)


# ============================================================
# SESSION STATE
# ============================================================

if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "customer_id" not in st.session_state:
    st.session_state.customer_id = None

if "current_balance" not in st.session_state:
    st.session_state.current_balance = None

if "profile_created" not in st.session_state:
    st.session_state.profile_created = False


# ============================================================
# PERSONAL INFORMATION
# ============================================================

st.header("👤 Personal Information")

col1, col2 = st.columns(2)

with col1:
    name = st.text_input(
        "Name *",
        placeholder="Enter your full name"
    )

with col2:
    email = st.text_input(
        "Email *",
        placeholder="example@gmail.com"
    )


# ============================================================
# MONTHLY FINANCIAL INFORMATION
# ============================================================

st.header("📅 Monthly Financial Information")

st.info(
    "Income and Budget are entered once for the month. "
    "They are not entered again for every transaction."
)

col1, col2, col3 = st.columns(3)

with col1:
    income = st.number_input(
        "Monthly Income (₹) *",
        min_value=0.0,
        step=100.0,
        value=0.0
    )

with col2:
    budget = st.number_input(
        "Monthly Budget (₹) *",
        min_value=0.0,
        step=100.0,
        value=0.0
    )

with col3:
    opening_balance = st.number_input(
        "Opening Account Balance (₹) *",
        min_value=0.0,
        step=100.0,
        value=0.0
    )


# ============================================================
# CREATE PROFILE
# ============================================================

if st.button(
    "Create / Update Monthly Profile",
    type="primary"
):

    errors = []

    # Name validation
    if not name.strip():
        errors.append("Name is required.")

    # Email validation
    if not email.strip():
        errors.append("Email is required.")

    elif "@" not in email or "." not in email:
        errors.append("Please enter a valid email address.")

    # Income validation
    if income <= 0:
        errors.append("Monthly income must be greater than ₹0.")

    # Budget validation
    if budget <= 0:
        errors.append("Monthly budget must be greater than ₹0.")

    # Opening balance validation
    if opening_balance < 0:
        errors.append("Opening balance cannot be negative.")

    # Budget cannot exceed income
    if budget > income:
        errors.append(
            "Monthly budget should not be greater than monthly income."
        )

    if errors:

        for error in errors:
            st.error(error)

    else:

        # Generate customer ID
        st.session_state.customer_id = (
            "CUST-" +
            str(uuid.uuid4())[:8].upper()
        )

        # Set current balance
        st.session_state.current_balance = opening_balance

        st.session_state.profile_created = True

        st.success("Monthly profile created successfully!")

        st.write(
            f"**Customer ID:** "
            f"{st.session_state.customer_id}"
        )

        st.write(
            f"**Current Balance:** "
            f"₹{st.session_state.current_balance:,.2f}"
        )


# ============================================================
# TRANSACTION SECTION
# ============================================================

if st.session_state.profile_created:

    st.header("💳 Add Transaction")

    st.write(
        "Fields marked with * are required."
    )

    with st.form("transaction_form"):

        col1, col2 = st.columns(2)

        # ----------------------------------------------------
        # TRANSACTION AMOUNT
        # ----------------------------------------------------

        with col1:

            transaction_amount = st.number_input(
                "Transaction Amount (₹) *",
                min_value=0.01,
                step=100.0,
                value=None,
                placeholder="Enter amount"
            )

        # ----------------------------------------------------
        # TRANSACTION DATE
        # ----------------------------------------------------

        with col2:

            transaction_date = st.date_input(
                "Transaction Date *"
            )

        # ----------------------------------------------------
        # TRANSACTION TIME
        # ----------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            transaction_time = st.time_input(
                "Transaction Time *"
            )

        # ----------------------------------------------------
        # CATEGORY
        # ----------------------------------------------------

        with col2:

            category = st.text_input(
                "Category *",
                placeholder="Food, Shopping, Transport..."
            )

        # ----------------------------------------------------
        # MERCHANT
        # ----------------------------------------------------

        merchant = st.text_input(
            "Merchant *",
            placeholder="Amazon, Uber, Zomato..."
        )
        
        # ----------------------------------------------------
        # SUBMIT
        # ----------------------------------------------------

        submitted = st.form_submit_button(
            "➕ Add Transaction",
            type="primary"
        )

    # ========================================================
    # PROCESS TRANSACTION
    # ========================================================

    if submitted:

        errors = []

        # Amount validation
        if transaction_amount is None:
            errors.append(
                "Transaction amount is required."
            )

        elif transaction_amount <= 0:
            errors.append(
                "Transaction amount must be greater than ₹0."
            )

        # Category validation
        if not category.strip():
            errors.append(
                "Category is required."
            )

        # Merchant validation
        if not merchant.strip():
            errors.append(
                "Merchant is required."
            )

        # DateTime validation
        try:

            date_time = datetime.strptime(
                datetime_input,
                "%Y-%m-%d %H:%M:%S"
            )

        except ValueError:

            errors.append(
                "DateTime must be in "
                "YYYY-MM-DD HH:MM:SS format."
            )

            date_time = None

        # Check balance
        if (
            transaction_amount is not None
            and transaction_amount
            > st.session_state.current_balance
        ):

            errors.append(
                "Transaction amount cannot be greater "
                "than the available account balance."
            )

        # ====================================================
        # IF ERRORS
        # ====================================================

        if errors:

            for error in errors:
                st.error(error)

        # ====================================================
        # ADD TRANSACTION
        # ====================================================

        else:

            # Generate Transaction ID
            transaction_id = (
                "TXN-" +
                str(uuid.uuid4())[:8].upper()
            )

            # Automatically calculate fields
            transaction_day = date_time.strftime(
                "%A"
            )

            transaction_month = date_time.strftime(
                "%B"
            )

            is_weekend = (
                1
                if date_time.weekday() >= 5
                else 0
            )

            # Automatically deduct transaction
            st.session_state.current_balance -= (
                transaction_amount
            )

            # Create transaction dictionary
            transaction = {

                "TransactionID":
                    transaction_id,

                "Name":
                    name,

                "Email":
                    email,

                "Income":
                    income,

                "Budget":
                    budget,

                "TransactionAmount":
                    transaction_amount,

                "TransactionDate":
                    transaction_date.strftime(
                        "%Y-%m-%d"
                    ),

                "TransactionTime":
                    transaction_time.strftime(
                        "%H:%M:%S"
                    ),

                "Category":
                    category.strip(),

                "Merchant":
                    merchant.strip(),

                "CustAccountBalance":
                    st.session_state.current_balance,

                "TransactionDay":
                    transaction_day,

                "TransactionMonth":
                    transaction_month,

                "IsWeekend":
                    is_weekend
            }

            # Add to session state
            st.session_state.transactions.append(
                transaction
            )

            st.success(
                f"Transaction {transaction_id} "
                "added successfully!"
            )

            st.info(
                f"💰 Remaining Account Balance: "
                f"₹{st.session_state.current_balance:,.2f}"
            )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

if st.session_state.transactions:

    st.header("📊 Transaction History")

    data = pd.DataFrame(
        st.session_state.transactions
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

if st.session_state.transactions:

    st.header("📈 Financial Summary")

    data = pd.DataFrame(
        st.session_state.transactions
    )

    total_spending = data[
        "TransactionAmount"
    ].sum()

    remaining_balance = (
        st.session_state.current_balance
    )

    savings = income - total_spending

    spending_percentage = (
        (total_spending / income) * 100
        if income > 0
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Monthly Income",
            f"₹{income:,.2f}"
        )

    with col2:

        st.metric(
            "Total Spending",
            f"₹{total_spending:,.2f}"
        )

    with col3:

        st.metric(
            "Savings",
            f"₹{savings:,.2f}"
        )

    with col4:

        st.metric(
            "Remaining Balance",
            f"₹{remaining_balance:,.2f}"
        )

    st.write(
        f"**Spending Percentage:** "
        f"{spending_percentage:.2f}%"
    )
