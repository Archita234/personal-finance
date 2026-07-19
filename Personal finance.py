import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
from datetime import datetime, timedelta ,time
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, r2_score
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans

# First dataset
data1 = pd.read_csv('bank_transactions.csv')

data1 = data1.drop(["CustomerID","CustomerDOB","CustGender"],axis =1)

data1.rename(columns={"TransactionAmount (INR)": "TransactionAmount"}, inplace=True)

data1["TransactionTime"] = (
    data1["TransactionTime"]
    .astype(int)          # 143207.0 -> 143207
    .astype(str)          # "143207"
    .str.zfill(6)         # Ensures 6 digits (e.g. "093015")
)

data1["TransactionTime"] = pd.to_datetime(
    data1["TransactionTime"],
    format="%H%M%S"
).dt.time

data1["DateTime"] = pd.to_datetime(
    data1["TransactionDate"].astype(str) + " " + data1["TransactionTime"].astype(str),
    format="%d-%m-%Y %H:%M:%S"
)

data1["TransactionDay"] = data1["DateTime"].dt.day_name()
data1["TransactionMonth"] = data1["DateTime"].dt.month_name()
data1["EventDate"] = data1["DateTime"].dt.day

rows = []
for i in range(len(data1)):
  if data1.loc[i, "TransactionDay"] == "Saturday" or data1.loc[i, "TransactionDay"] == "Sunday":
    data1.loc[i, "IsWeekend"] = 1
  else:
    data1.loc[i, "IsWeekend"] = 0

#second dataset
categories = [
    "Food & Dining",
    "Groceries",
    "Shopping",
    "Travel",
    "Fuel",
    "Utilities",
    "Mobile & Internet",
    "Entertainment",
    "Healthcare",
    "Education",
    "Personal Care",
    "Investments",
    "Miscellaneous"
]
paymentType = ["Credit","Debit"]

PaymentMode = {
    "Credit": ["Bank Transfer", "Cash Deposit", "Interest Credit"],
    "Debit": ["ATM Withdrawal", "UPI"]
}



merchants = {
    "Food & Dining": ["Domino's", "McDonald's", "KFC", "Starbucks"],
    "Groceries": ["D-Mart", "Reliance Fresh", "Blinkit", "Zepto"],
    "Shopping": ["Amazon", "Flipkart", "Myntra", "Ajio"],
    "Travel": ["Uber", "Ola", "IRCTC", "Rapido"],
    "Fuel": ["Indian Oil", "HP Petrol Pump", "Bharat Petroleum"],
    "Utilities": ["Electricity Board", "Water Department", "Gas Agency"],
    "Mobile & Internet": ["Jio", "Airtel", "Vi"],
    "Entertainment": ["Netflix", "BookMyShow", "Spotify"],
    "Healthcare": ["Apollo Pharmacy", "MedPlus", "Fortis Hospital"],
    "Education": ["Coursera", "Udemy", "College Fee"],
    "Personal Care": ["Nykaa", "Salon", "Barber Shop"],
    "Investments": ["Groww", "Zerodha", "Mutual Fund SIP"],
    "Salary": ["ABC Pvt Ltd", "XYZ Technologies"],
    "Miscellaneous": ["Local Shop", "Gift Store"]
}

customerID = []
rows = []
for i in range(1,500):
     customerID.append(f"C0{i}")


for i in range(len(data1)):

    category = random.choice(categories)
    merchant = random.choice(merchants[category])
    PaymentType = random.choice(paymentType)
    paymentmode = random.choice(PaymentMode[PaymentType])
    CustomerID = random.choice(customerID)

    rows.append({
        "TransactionID": f"T{i}",
        "CustomerID": CustomerID,
        "Category": category,
        "Merchant": merchant,
        "PaymentType" : PaymentType,
        "PaymentMode" : paymentmode
    })

data2 = pd.DataFrame(rows)

#Third Dataset
Months = ["January","February","March","April","May","June","July","August","September","October","November","December"]

row = []
row = []

for customer in customerID:
  base_income = random.randint(60000, 100000)

  for month in Months:

    income = base_income + random.randint(-2000, 3000)
    budget = random.randint(int(0.6 * income), int(0.9 * income))

    row.append({
            "CustomerID": customer,
            "TransactionMonth": month,
            "Income": income,
            "Budget": budget
        })

data3 = pd.DataFrame(row)

#Merging three dataset
data = pd.merge(data1,data2,on = "TransactionID")
data = pd.merge(data,data3,on = ["CustomerID","TransactionMonth"], how = 'inner')

# columns from list
data.columns.tolist

# 3 more columns (Monthly_Spending)
data["Monthly_Spending"] = data.groupby("CustomerID")["TransactionAmount"].transform("sum")
data["Savings"] = data["Budget"] - data["Monthly_Spending"]
data["Investment"] = data["Income"] - data["Budget"]

for i in range(len(data)):
  if (
        data.loc[i, "TransactionAmount"] <= 0 or
        data.loc[i, "Monthly_Spending"] > data.loc[i, "Budget"] or
        data.loc[i, "Monthly_Spending"] > 0.8 * data.loc[i, "Income"] or
        data.loc[i, "Savings"] < 0.25 * data.loc[i, "Budget"] or
        data.loc[i, "Savings"] > 5 * data.loc[i, "Income"] or
        time(0, 0, 0) <= data.loc[i, "TransactionTime"] <= time(4, 0, 0) or
        data.loc[i, "Savings"] < data.loc[i, "Monthly_Spending"] or
        data.loc[i, "TransactionAmount"] * 0.8 > data.loc[i, "Income"]
        and (data.loc[i, "EventDate"] <= 7)
    ):
        data.loc[i, "Is_Anomaly"] = 1
  else:
        data.loc[i, "Is_Anomaly"] = 0
data[data["Is_Anomaly"] == 0]

# Start every customer's score at 0
data["HealthScore"] = 0

for i in range(len(data)):

    score = 0

    spending_ratio = data.loc[i, "Monthly_Spending"] / data.loc[i, "Income"]

    if spending_ratio <= 0.60:
        score += 30
    elif spending_ratio <= 0.80:
        score += 25
    elif spending_ratio <= 1.00:
        score += 15
    else:
        score += 5

    savings_ratio = data.loc[i, "Savings"] / data.loc[i, "Income"]
    if savings_ratio >= 0.30:
        score += 20
    elif savings_ratio >= 0.20:
        score += 15
    elif savings_ratio >= 0.10:
        score += 10
    elif savings_ratio >= 0:
        score += 5
    else:
        score += 0

    if data.loc[i, "Monthly_Spending"] <= data.loc[i, "Budget"]:
        score += 15
    else:
        score += 5

    investment_ratio = data.loc[i, "Investment"] / data.loc[i, "Income"]

    if investment_ratio >= 0.10:
        score += 10
    elif investment_ratio >= 0.05:
        score += 7
    elif investment_ratio > 0:
        score += 5
    else:
        score += 0

    balance = data.loc[i, "CustAccountBalance"]
    spending = data.loc[i, "Monthly_Spending"]

    if balance >= 3 * spending:
        score += 15
    elif balance >= spending:
        score += 10
    elif balance >= 0.5 * spending:
        score += 5
    else:
        score += 0

    # 6. Behaviour Score (10)
    behaviour = 10

    if data.loc[i, "Is_Anomaly"] == 1:
        behaviour -= 5

    if data.loc[i, "IsWeekend"] == 1:
        behaviour -= 2

    if behaviour < 0:
        behaviour = 0

    score += behaviour

    # Final Score
    data.loc[i, "HealthScore"] = score


def category(score):

    if score >= 90:
        return "Excellent"

    elif score >= 75:
        return "Good"

    elif score >= 60:
        return "Average"

    elif score >= 40:
        return "Poor"

    else:
        return "Critical"


data["HealthCategory"] = data["HealthScore"].apply(category)

data = data.dropna()
print(data)
data.info()


plt.hist(data["TransactionAmount"], bins=30)
plt.xlabel("Transaction Amount")
plt.ylabel("Frequency")
plt.title("Distribution of Transaction Amount")
plt.show()

Monthly_Spending = data.groupby('TransactionMonth')['TransactionAmount'].sum().reset_index()

print(Monthly_Spending)
plt.figure(figsize=(12,10))
plt.plot(
    Monthly_Spending['TransactionMonth'],
    Monthly_Spending['TransactionAmount'],
    color = 'red',
    marker = 'o',
    linestyle = '--'
)
plt.title("Monthly Spending Trend", fontsize=18, fontweight='bold')
plt.xlabel("Month", fontsize=13)
plt.ylabel("Amount Spent (₹)", fontsize=13)

plt.xticks(rotation=0)
plt.show()

category_spending = data.groupby('Category')['TransactionAmount'].sum().reset_index()
category_spending
plt.figure(figsize=(15,5))

plt.bar(
    category_spending['Category'],
    category_spending['TransactionAmount'],
    color = 'blue'
)

plt.title("Total Amount Spent by Category")
plt.xlabel("Category")
plt.ylabel("Amount")

plt.tight_layout()
plt.show()

daily_Spending = data.groupby('EventDate')['TransactionAmount'].sum().reset_index()
sns.scatterplot(x = 'EventDate' , y = 'TransactionAmount', data = daily_Spending)
plt.show()

top_customers = (
    data.groupby("CustomerID")["TransactionAmount"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

plt.figure(figsize=(12,6))

sns.barplot(
    data=top_customers,
    x="CustomerID",
    y="TransactionAmount"
)

plt.title("Top 10 Spending Customers", fontsize=16, fontweight="bold")
plt.xlabel("Customer ID")
plt.ylabel("Total Amount Spent (₹)")
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()

ax = sns.countplot(
    data = data,
    x = "PaymentType",
    order = data['PaymentType'].value_counts().index
)
plt.title("Payment Type Distribution", fontsize=18, weight="bold")
plt.xlabel("Payment Type")
plt.ylabel("Number of Transactions")
plt.xticks(rotation=30)

for container in ax.containers:
    ax.bar_label(container)

plt.tight_layout()
plt.show()

merchant = data.groupby("Merchant")["TransactionAmount"].sum().sort_values(ascending=False)

merchant.head(10).plot(kind="bar", color = "green")
plt.title("Top 10 Merchants")
plt.show()

#Payment Mode Usage
data["PaymentMode"].value_counts().plot(kind = "pie", autopct="%1.1f%%")
plt.ylabel('')
plt.title("Payment Mode Usage")
plt.show()

week = data.groupby("IsWeekend")["TransactionAmount"].mean()
week.index = ["Weekday", "Weekend"]

week.plot(kind="bar")
plt.ylabel("Average Spending")
plt.xticks(rotation = 0)
plt.title("Average Spending By Week")
plt.show()

plt.hist(data["HealthScore"])
plt.title("Financial Health Score Distribution")
plt.show()

data["HealthCategory"].value_counts().plot(kind="bar")
plt.title("Financial Health Categories")
plt.show()

plt.figure(figsize=(10,8))
sns.heatmap(
    data.select_dtypes(include="number").corr(),
    annot=True,
    cmap="coolwarm"
)
plt.show()

plt.scatter(data["Income"], data["Monthly_Spending"])

plt.xlabel("Income")
plt.ylabel("Monthly Spending")
plt.title("Income vs Spending")
plt.show()

data["Is_Anomaly"].value_counts().plot(kind = 'pie', autopct="%1.1f%%")
plt.title("Anomaly Distribution")
plt.show()


plt.figure(figsize=(10,6))

sns.histplot(data["Savings"])
plt.title("Savings Distribution")
plt.xlabel("Savings")
plt.ylabel("Number of Records")

plt.tight_layout()
plt.show()


X = data[[
    "Income",
    "Budget",
    "TransactionAmount",
    "CustAccountBalance",
    "Monthly_Spending"
]]

y = data["Is_Anomaly"]

X_train,X_test, y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42)

model_Logistic = LogisticRegression()
model_Logistic.fit(X_train,y_train)
lr = model_Logistic.predict(X_test)

model_Ridge = RidgeClassifier(alpha = 1.0)
model_Ridge.fit(X_train,y_train)
rg = model_Ridge.predict(X_test)

model_DecisonTree = DecisionTreeRegressor()
model_DecisonTree.fit(X_train,y_train)
dt = model_DecisonTree.predict(X_test)

model_random = RandomForestClassifier(random_state=42)
model_random.fit(X_train, y_train)
rf = model_random.predict(X_test)

print("====Model Performance====")
print("Logistic:\n", classification_report(y_test, lr))
print("Decision Tree:\n", classification_report(y_test, dt))
print("Ridge:\n",classification_report(y_test, rg))
print("Random Forest:\n", classification_report(y_test, rf))

print("====Model Performance====")
print("Logistic: ",accuracy_score(y_test, lr))
print("Decision Tree: ",accuracy_score(y_test, dt))
print("Ridge:", accuracy_score(y_test,rg))
print("Random Forest:", accuracy_score(y_test, rf))

importance = pd.Series(
    model_random.feature_importances_,
    index=X.columns
)

importance.sort_values().plot(kind="barh")
plt.title("Feature Importance on Anomaly Detection")
plt.show()

model_kmeans = KMeans(
    n_clusters=3,
    random_state=42
)

cluster = model_kmeans.fit_predict(X)
sns.scatterplot(data=data,x="Income",y="TransactionAmount",hue=cluster)

X = data[[
    "Income",
    "Budget",
    "TransactionAmount",
    "CustAccountBalance",
    "Monthly_Spending"
]]

y = data["HealthScore"]

X_train,X_test, y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42)

model_Logistic = LogisticRegression()
model_Logistic.fit(X_train,y_train)
lr = model_Logistic.predict(X_test)

model_Ridge = RidgeClassifier(alpha = 1.0)
model_Ridge.fit(X_train,y_train)
rg = model_Ridge.predict(X_test)

model_DecisonTree = DecisionTreeRegressor()
model_DecisonTree.fit(X_train,y_train)
dt = model_DecisonTree.predict(X_test)

model_random = RandomForestClassifier(random_state=42)
model_random.fit(X_train, y_train)
rf = model_random.predict(X_test)

print("====Model Performance====")
print("Logistic:\n", classification_report(y_test, lr))
print("Decision Tree:\n", classification_report(y_test, dt))
print("Ridge:\n",classification_report(y_test, rg))
print("Random Forest:\n", classification_report(y_test, rf))

print("====Model Performance====")
print("Logistic: ",accuracy_score(y_test, lr))
print("Decision Tree: ",accuracy_score(y_test, dt))
print("Ridge:", accuracy_score(y_test,rg))
print("Random Forest:", accuracy_score(y_test, rf))

importance = pd.Series(
    model_random.feature_importances_,
    index=X.columns
)

importance.sort_values().plot(kind="barh")
plt.title("Feature Importance On Health Score")
plt.show()

model_kmeans = KMeans(
    n_clusters=3,
    random_state=42
)

cluster = model_kmeans.fit_predict(X)
sns.scatterplot(data=data,x="Income",y="TransactionAmount",hue=cluster)