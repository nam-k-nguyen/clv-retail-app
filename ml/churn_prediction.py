from dotenv import load_dotenv
import mysql.connector
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

load_dotenv()
host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
database = os.getenv("DB_NAME")

# Load uploaded CSV
transactions = pd.read_csv("./data/400_transactions.csv")
transactions.rename(
    columns={
        "BASKET_NUM                      ": "basket_num",
        "HSHD_NUM        ": "hshd_num",
        "PURCHASE_": "purchase_date",
        "PRODUCT_NUM                     ": "product_num",
        "     SPEND": "spend",
        "     UNITS": "units",
        "STORE_R": "store_region",
        "  WEEK_NUM": "week_num",
        "YEAR": "year",
    },
    inplace=True,
)

households = pd.read_csv("./data/400_households.csv")
households.rename(
    columns={
        "HSHD_NUM        ": "hshd_num",
        "L": "loyalty_flag",
        "AGE_RANGE                                                                                                                                                                                               ": "age_range",
        "MARITAL": "marital_status",
        "INCOME_RANGE                                                                                                                                                                                            ": "income_range",
        "HOMEOWNER": "homeowner",
        "HSHD_COMPOSITION ": "hshd_composition",
        "HH_SIZE                                                                                                                                                                                                 ": "hh_size",
        "CHILDREN": "children",
    },
    inplace=True,
)

conn = mysql.connector.connect(
    host=host,  # Your host, usually localhost
    user=user,  # Your full username
    password=password,  # Your actual password
    database=database,  # ssl_verify_identity=True,
    ssl_disabled=False,
    ssl_ca="BaltimoreCyberTrustRoot.crt.pem",  # Make sure this file exists in your working dir
    port=3306,
)

# Merge datasets on hshd_num
merged = pd.merge(transactions, households, on="hshd_num", how="left")

# Feature engineering
agg = (
    merged.groupby("hshd_num")
    .agg(
        {
            "spend": ["sum", "mean"],
            "basket_num": "nunique",
            "week_num": ["max", "min", "nunique"],
            "loyalty_flag": "first",
            "hh_size": "first",
            "income_range": "first",
            "children": "first",
        }
    )
    .reset_index()
)

agg.columns = [
    "hshd_num",
    "total_spend",
    "avg_spend",
    "basket_count",
    "last_week",
    "first_week",
    "active_weeks",
    "loyalty_flag",
    "hh_size",
    "income_range",
    "children",
]

# Convert week 45 cutoff to define churn
agg["churned"] = (agg["last_week"] < 45).astype(int)

# Clean categorical and missing data
agg["loyalty_flag"] = (agg["loyalty_flag"] == "Y").astype(int)
agg["hh_size"] = (
    agg["hh_size"]
    .astype(str)  # convert to string to handle strip
    .str.strip()  # remove extra spaces
    .replace("5+", "5")  # replace '5+' after trimming
    .replace("null", "0")  # treat NaNs converted to 'nan' as zero
    .astype(int)  # convert to integer
)
agg["children"] = pd.to_numeric(agg["children"], errors="coerce").fillna(0).astype(int)
agg["income_range"] = agg["income_range"].astype("category").cat.codes

# Split data
X = agg[
    [
        "total_spend",
        "avg_spend",
        "basket_count",
        "active_weeks",
        "loyalty_flag",
        "hh_size",
        "income_range",
        "children",
    ]
]
y = agg["churned"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)


# Feature importance
importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(
    ascending=False
)
importances = importances.reset_index()
importances.columns = ["feature", "importance"]

print(importances)

importances.to_csv("data/churn_prediction.csv", index=False)


# optional report
# import matplotlib.pyplot as plt
# import seaborn as sns

# sns.set(style="whitegrid")
# plt.figure(figsize=(10, 5))
# sns.barplot(x=importances, y=importances.index, palette="viridis")
# plt.title("Churn Prediction - Feature Importance")
# plt.xlabel("Importance Score")
# plt.ylabel("Feature")
# plt.tight_layout()
# plt.show()

# # Output performance
# report = classification_report(y_test, y_pred, output_dict=True)
# pd.DataFrame(report).T

# conn.close()
