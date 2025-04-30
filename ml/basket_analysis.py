# Run this file to update

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
df = pd.read_csv("./data/400_transactions.csv").rename(
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

conn = mysql.connector.connect(
    host=host, # Your host, usually localhost
    user=user, # Your full username
    password=password, # Your actual password
    database=database, # ssl_verify_identity=True,
    ssl_disabled=False,
    ssl_ca="BaltimoreCyberTrustRoot.crt.pem",  # Make sure this file exists in your working dir
    port=3306,
)

# === QUERY THE TRANSACTIONS TABLE ===
query = "SELECT basket_num, product_num FROM transactions WHERE basket_num IS NOT NULL AND product_num IS NOT NULL;"
df = pd.read_sql(query, conn)

# Drop NaNs and convert to string
df = df[["basket_num", "product_num"]].dropna()
df["basket_num"] = df["basket_num"].astype(str)
df["product_num"] = df["product_num"].astype(str)

# Limit to top 50 products
top_products = df["product_num"].value_counts().head(50).index
df = df[df["product_num"].isin(top_products)]

# Limit to top 5000 baskets
top_baskets = df["basket_num"].value_counts().head(5000).index
df = df[df["basket_num"].isin(top_baskets)]

# One-hot encode basket-product presence
basket_df = (
    df.groupby(["basket_num", "product_num"])["product_num"].count().unstack().fillna(0)
)
basket_df[basket_df > 0] = 1

# Choose a target product to predict
target_product = basket_df.columns[0]  # Or choose one explicitly
X = basket_df.drop(columns=[target_product])
y = basket_df[target_product]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train Random Forest
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Predict and report
y_pred = clf.predict(X_test)
print(f"\n🎯 Predicting product: {target_product}")
print(classification_report(y_test, y_pred))

# Feature importances (top predictors)
importances = pd.Series(clf.feature_importances_, index=X.columns)
importances = importances.reset_index()
importances.columns = ["product_num", "score"]


conn.close()

importances.sort_values(ascending=False, by="score").to_csv("data/top_cross_sell_predictors.csv", index=False)

