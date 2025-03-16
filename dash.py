import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from babel.numbers import format_currency

# Load Data
file_path = "all_data.csv"

try:
    all_data = pd.read_csv(file_path, parse_dates=["order_purchase_timestamp"])
except FileNotFoundError:
    st.error(f"File '{file_path}' tidak ditemukan. Pastikan file tersebut ada di direktori yang benar.")
    st.stop()

# Streamlit App Configuration
st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")

# Sidebar Filters
st.sidebar.header("Filter Data")
selected_states = st.sidebar.multiselect("Pilih Wilayah:", sorted(all_data["customer_state"].dropna().unique()), default=[])
selected_products = st.sidebar.multiselect("Pilih Produk:", sorted(all_data["product_category_name_english"].dropna().unique()), default=[])

# Filter berdasarkan rentang tanggal
min_date = all_data["order_purchase_timestamp"].min()
max_date = all_data["order_purchase_timestamp"].max()
start_date, end_date = st.sidebar.date_input("Pilih Rentang Tanggal:", [min_date, max_date], min_value=min_date, max_value=max_date)

# Filter data berdasarkan pilihan pengguna
filtered_data = all_data[(all_data["order_purchase_timestamp"] >= pd.to_datetime(start_date)) &
                          (all_data["order_purchase_timestamp"] <= pd.to_datetime(end_date))]

if selected_states:
    filtered_data = filtered_data[filtered_data["customer_state"].isin(selected_states)]

if selected_products:
    filtered_data = filtered_data[filtered_data["product_category_name_english"].isin(selected_products)]

# Header
st.title("📊 E-Commerce Data Analysis Dashboard")


# ---- VISUALISASI 1: Pendapatan Tertinggi & Terendah Berdasarkan Kategori Produk ----
st.subheader("📦 Pendapatan Tertinggi & Terendah Berdasarkan Kategori Produk")

product_revenue = filtered_data.groupby("product_category_name_english")["price"].sum().reset_index()
top_products_df = product_revenue.sort_values("price", ascending=False).head(10)
bottom_products_df = product_revenue.sort_values("price", ascending=True).head(10)

fig, ax = plt.subplots(1, 2, figsize=(20, 5))
colors_top = ["#008080" if i == 0 else "#20B2AA" for i in range(len(top_products_df))]
colors_bottom = ["#FF8C00" if i == 0 else "#FFA07A" for i in range(len(bottom_products_df))]

sns.barplot(data=top_products_df, 
            x="product_category_name_english", 
            y="price", 
            palette=colors_top, 
            ax=ax[0]
)

ax[0].set_title("Top 10 Produk dengan Pendapatan Tertinggi (BRL)")
ax[0].set_xticklabels(ax[0].get_xticklabels(), rotation=45, ha="right")

for i, v in enumerate(top_products_df["price"]):
    ax[0].text(i, v + (0.01 * max(top_products_df["price"])), str(int(v)), ha='center', color='black')

sns.barplot(data=bottom_products_df, 
            x="product_category_name_english", 
            y="price", 
            palette=colors_bottom, 
            ax=ax[1]
)

ax[1].set_title("Top 10 Produk dengan Pendapatan Terendah (BRL)")
ax[1].set_xticklabels(ax[1].get_xticklabels(), rotation=45, ha="right")

for i, v in enumerate(bottom_products_df["price"]):
    ax[1].text(i, v + (0.01 * max(bottom_products_df["price"])), str(int(v)), ha='center', color='black')

st.pyplot(fig)


# ---- VISUALISASI 2: Jumlah Pesanan Tiap Bulan ----
st.subheader("📅 Jumlah Pesanan Tiap Bulan")

filtered_data["year_month"] = filtered_data["order_purchase_timestamp"].dt.to_period("M")
transactions_per_month = filtered_data.groupby("year_month")["order_id"].count().reset_index()
transactions_per_month["year_month"] = transactions_per_month["year_month"].astype(str)

fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(
    data=transactions_per_month, 
    x="year_month", 
    y="order_id", 
    marker="o", 
    color="b", 
    linewidth=2)

ax.set_xlabel("Bulan")
ax.set_ylabel("Jumlah Pesanan")
ax.set_title("Jumlah Pesanan Tiap Bulan")
plt.xticks(rotation=45)
st.pyplot(fig)


# ---- VISUALISASI 3: Status Pesanan ----
st.subheader("📦 Status Pesanan")

status_counts = filtered_data["order_status"].value_counts().reset_index()
status_counts.columns = ["order_status", "count"]

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(data=status_counts, 
            x="order_status", 
            y="count", 
            palette="deep", 
            ax=ax
)

ax.set_title("Distribusi Status Pesanan")

for i, v in enumerate(status_counts["count"]):
    ax.text(i, v + (0.01*max(status_counts["count"])), str(v), ha='center', color='black')

st.pyplot(fig)


# ---- VISUALISASI 4: Wilayah dengan Pembatalan Tertinggi ----
st.subheader("📍 Wilayah dengan Pembatalan Tertinggi")

canceled_orders = filtered_data[filtered_data["order_status"] == "canceled"].groupby("customer_state")["order_id"].count().reset_index()
canceled_orders.columns = ["customer_state", "canceled_count"]
canceled_orders = canceled_orders.sort_values(by="canceled_count", ascending=False)

fig, ax = plt.subplots(figsize=(12, 6))
colors = ["darkblue" if i == 0 else "lightblue" for i in range(len(canceled_orders))]

sns.barplot(data=canceled_orders, 
            x="customer_state", 
            y="canceled_count", 
            palette=colors, 
            ax=ax
)

ax.set_title("Jumlah Pembatalan Pesanan per Wilayah")

for i, v in enumerate(canceled_orders["canceled_count"]):
    ax.text(i, v + (0.01*max(canceled_orders["canceled_count"])), str(v), ha='center', color='black')

st.pyplot(fig)


# ---- VISUALISASI 5: RFM ANALYSIS ----

st.subheader("👤 Top Pelanggan Berdasarkan Parameter Recency, Frequency, dan Monetary")

# Menghitung total belanja per order_id
orders_summary_df = filtered_data.groupby("order_id").agg(
    total_product_value=("price", "sum"),
    total_freight_value=("freight_value", "sum")
).reset_index()

# Menambahkan kolom total_order_value
orders_summary_df["total_order_value"] = orders_summary_df["total_product_value"] + orders_summary_df["total_freight_value"]

# Menghitung total belanja per pelanggan
customer_spending_df = orders_summary_df.merge(
    filtered_data[["order_id", "customer_unique_id", "order_purchase_timestamp"]],
    on="order_id",
    how="left"
)

# Menentukan tanggal referensi (tanggal terakhir dalam dataset)
reference_date = filtered_data["order_purchase_timestamp"].max()

# Menghitung RFM
rfm_df = customer_spending_df.groupby("customer_unique_id").agg({
    "order_purchase_timestamp": lambda x: (reference_date - x.max()).days,
    "order_id": "nunique",
    "total_order_value": "sum"
}).reset_index()

rfm_df.columns = ["customer_unique_id", "Recency", "Frequency", "Monetary"]

# Menghitung rata-rata RFM
avg_recency = round(rfm_df["Recency"].mean(), 1)
avg_frequency = round(rfm_df["Frequency"].mean(), 2)
avg_monetary = format_currency(rfm_df["Monetary"].mean(), "BRL", locale='pt_BR')

# Menampilkan metrik
col1, col2, col3 = st.columns(3)
col1.metric("📅 Average Recency (days)", avg_recency)
col2.metric("🛒 Average Frequency", avg_frequency)
col3.metric("💰 Average Monetary", avg_monetary)

# Visualisasi Top 5 Pelanggan berdasarkan RFM
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 10))
colors = ["#69b3a2"] * 5

# Fungsi untuk menambahkan nilai label
def add_value_labels(ax):
    for p in ax.patches:
        ax.annotate(f"{p.get_height():,.0f}",
                    (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha='center', va='bottom', fontsize=15, fontweight="bold")

def adjust_x_labels(ax, data):
    ax.set_xticklabels(data["customer_unique_id"], rotation=45, ha="right")

# Top 5 Recency
recency_data = rfm_df.sort_values(by="Recency", ascending=True).head(5)
sns.barplot(y=recency_data["Recency"], 
            x=recency_data["customer_unique_id"], 
            palette=colors, 
            ax=ax[0]
)
ax[0].set_title("Top 5 Customers by Recency", fontsize=25)
ax[0].set_xlabel("Customer Unique ID", fontsize=20)
ax[0].set_ylabel("Recency (days)", fontsize=20)
ax[0].tick_params(axis='x', labelsize=15)
ax[0].tick_params(axis='y', labelsize=15)
add_value_labels(ax[0])
adjust_x_labels(ax[0], recency_data)

# Top 5 Frequency
frequency_data = rfm_df.sort_values(by="Frequency", ascending=False).head(5)
sns.barplot(y=frequency_data["Frequency"], 
            x=frequency_data["customer_unique_id"], 
            palette=colors, 
            ax=ax[1]
)
ax[1].set_title("Top 5 Customers by Frequency", fontsize=25)
ax[1].set_xlabel("Customer Unique ID", fontsize=20)
ax[1].set_ylabel("Frequency (orders)", fontsize=20)
ax[1].tick_params(axis='x', labelsize=15)
ax[1].tick_params(axis='y', labelsize=15)
add_value_labels(ax[1])
adjust_x_labels(ax[1], frequency_data)

# Top 5 Monetary
monetary_data = rfm_df.sort_values(by="Monetary", ascending=False).head(5)
sns.barplot(y=monetary_data["Monetary"], 
            x=monetary_data["customer_unique_id"], 
            palette=colors, 
            ax=ax[2]
)
ax[2].set_title("Top 5 Customers by Monetary", fontsize=25)
ax[2].set_xlabel("Customer Unique ID", fontsize=20)
ax[2].set_ylabel("Monetary (BRL)", fontsize=20)
ax[2].tick_params(axis='x', labelsize=15)
ax[2].tick_params(axis='y', labelsize=15)
add_value_labels(ax[2])
adjust_x_labels(ax[2], monetary_data)

st.pyplot(fig)


# Footer
st.markdown("**Dashboard by Aulaa Mustika_MC312D5X2481**")
