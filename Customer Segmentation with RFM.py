
###############################################################
# 1. Data Understanding
###############################################################

import datetime as dt
import pandas as pd

pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', lambda x: '%.3f' % x)

df_ = pd.read_excel("location", sheet_name="Year 2010-2011")
df = df_.copy()  # It takes time to read the file,thus a copy is taken after reading the file
# so we do not have to read the file and have to wait repeatedly.
df.head()
df.shape
df.isnull().sum()

# Number of unique products
df["Description"].nunique()

# Number of products appearing in invoices
df["Description"].value_counts().head()

# Most ordered product (including quantities)
df.groupby("Description").agg({"Quantity": "sum"}).sort_values("Quantity", ascending=False).head()

# Number of unique invoices
df["Invoice"].nunique()

# Add a new column for TotalPrice
df["TotalPrice"] = df["Quantity"] * df["Price"]

# Find the total cost in every invoice
df.groupby("Invoice").agg({"TotalPrice": "sum"}).head()


###############################################################
# 2. Data Preparation
###############################################################

df.shape  # To observe the reducing number of rows as we make adjustments
df.isnull().sum()  # Observed problem: Missing CustomerID data, needed to be erased
df.describe().T  # Observed problem: Negative Quantitity values,

df = df[(df['Quantity'] > 0)]  # To solve Negative Quantitity values problem

df.dropna(inplace=True)
# To solve Missing CustomerID data problem
# Inplace makes the changes on dataset immediately without a need for assigning

df["Invoice"] = df["Invoice"].astype(str)
df = df[~df["Invoice"].str.contains("C", na=False)]
# Cancelled invoices do not need to be in the analysis, so they are erased.
# ~ means except this

###############################################################
# 3. Calculating RFM Metrics
###############################################################

# Recency, Frequency, Monetary
df.head()
# Check the data

df["InvoiceDate"].max()  # latest date on data
today_date = dt.datetime(2011, 12, 11)

# added 2 days to last day to form today's date
# utilized datetime library so that today_date's datatype is datetime

rfm = df.groupby('Customer ID').agg({'InvoiceDate': lambda InvoiceDate: (today_date - InvoiceDate.max()).days,
                                     'Invoice': lambda Invoice: Invoice.nunique(),
                                     'TotalPrice': lambda TotalPrice: TotalPrice.sum()})

rfm.head()
# In order, Recency, Frequency, Monetary are found.
# Recency is the difference in the today's date and last purchase on Customer ID level.
# Frequency is the number of unique invoices that belongs to the same customer.
# Monetary is summation of total prices of the same customer, so we know how much each customer brings to the company.


rfm.columns = ['recency', 'frequency', 'monetary']
# change the column names
rfm.describe().T  # to control if there is an unsual situation
rfm = rfm[rfm["monetary"] > 0]
# min monetary = 0 is unusual, so they are excluded.
rfm.shape
# Analysis is customer spesific, so rfm table row number
# must be equal to unique Customer ID number.


###############################################################
# 4. Calculating RFM Scores
###############################################################

rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
# recency metrics divided 5 equal parts acoording to their sizes and
# labelled such a way that greatest recency got 1, the smallest recency got 5.

rfm["frequency_score"] = pd.qcut(rfm['frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
# the problem in frequency is some numbers are too repetitive that
# qcut function can not label the same frequency number diffently
# rank method solves this problem by assigning the first comer number to first label.

rfm["monetary_score"] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) +
                    rfm['frequency_score'].astype(str))
# by RFM definition, string is created with recency and frequency score
# and formed final RFM Score
# monetary score is necessary for observation, but it is not used in forming RFM Score

rfm.describe().T
# newly created scores did not apper with describe function
# since they are strings and not integers

rfm[rfm["RFM_SCORE"] == "55"]
# champions

rfm[rfm["RFM_SCORE"] == "11"]
# hibernating

###############################################################
# 5. Creating & Analysing RFM Segments
###############################################################
# regex
# RFM Naming (Pattern Matching)
seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}
#  Basically the R-F table is coded using regex.

rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)

segment_analysis = rfm[["segment", "recency", "frequency", "monetary"]].groupby("segment").agg(["mean", "count"])

rfm[rfm["segment"] == "cant_loose"].head()
cant_loose_customers = rfm[rfm["segment"] == "cant_loose"].index
#  A list of customers which the company should be more careful with is formed.

new_df = pd.DataFrame()
#  Empty dataframe is formed
new_df["new_customer_id"] = rfm[rfm["segment"] == "new_customers"].index
new_df["new_customer_id"] = new_df["new_customer_id"].astype(int)
#  To get rid of the decimals

new_df.to_csv("new_customers.csv")
rfm.to_csv("rfm.csv")


#  Segment information is extracted into an excel file.

###############################################################
# 6. Functionalization
###############################################################
# Clean version of all the code has been written above:


def create_rfm(dataframe, csv=False):
    # DATA PREPARARTION
    dataframe["TotalPrice"] = dataframe["Quantity"] * dataframe["Price"]
    dataframe.dropna(inplace=True)
    dataframe = dataframe[~dataframe["Invoice"].str.contains("C", na=False)]

    # RFM METRICS CALCULATION
    today_date = dt.datetime(2011, 12, 11)
    rfm = dataframe.groupby('Customer ID').agg({'InvoiceDate': lambda date: (today_date - date.max()).days,
                                                'Invoice': lambda num: num.nunique(),
                                                "TotalPrice": lambda price: price.sum()})
    rfm.columns = ['recency', 'frequency', "monetary"]
    rfm = rfm[(rfm['monetary'] > 0)]

    # RFM SCORES CALCULATION
    rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    rfm["monetary_score"] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

    # cltv_df skorları kategorik değere dönüştürülüp df'e eklendi
    rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) +
                        rfm['frequency_score'].astype(str))

    # CREATING AND ANALYSING RFM SEGMENTS
    seg_map = {
        r'[1-2][1-2]': 'hibernating',
        r'[1-2][3-4]': 'at_risk',
        r'[1-2]5': 'cant_loose',
        r'3[1-2]': 'about_to_sleep',
        r'33': 'need_attention',
        r'[3-4][4-5]': 'loyal_customers',
        r'41': 'promising',
        r'51': 'new_customers',
        r'[4-5][2-3]': 'potential_loyalists',
        r'5[4-5]': 'champions'
    }

    rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
    rfm = rfm[["recency", "frequency", "monetary", "segment"]]
    rfm.index = rfm.index.astype(int)

    #  if csv file is wanted, this added as argument to function
    if csv:
        rfm.to_csv("rfm.csv")

    return rfm


#  Since we have a function for RFM analysis, we can analyze Year 2009-2010 easily

df2_ = pd.read_excel("location", sheet_name="Year 2009-2010")
df2 = df2_.copy()

rfm_new = create_rfm(df2, csv=True)
