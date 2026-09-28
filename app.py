import streamlit as st
import pandas as pd
import datetime
import calendar

st.set_page_config(page_title="月度日均余额测算工具", layout="wide")

# ── 全局字体放大（移动端友好）─────────────────────────────────────────────
st.html("""
<style>
  /* 全局基准字号 */
  html, body, .stApp, .stApp * {
    font-size: 20px !important;
  }
  /* 标题层级放大 */
  h1 { font-size: 2rem !important; }
  h2 { font-size: 1.4rem !important; }
  h3 { font-size: 1.15rem !important; }
  /* 上传按钮放大 */
  .stFileUploader > div {
    font-size: 1rem !important;
  }
  /* 表格字号 */
  .stDataFrame, .stDataEditor, table {
    font-size: 16px !important;
  }
</style>
""")

st.title("🏦 银行账单月度日均余额 (DAB) 测算工具")
st.write("上传银行导出的 Excel 交易流水，自动推算全月每日余额并支持在线模拟测算。")

# 1. 文件上传区
uploaded_file = st.file_uploader("请选择银行导出的 Excel 账单文件 (.xls / .xlsx)", type=["xls", "xlsx"])

if uploaded_file is not None:
 try:
  # 2. 读取与解析原始账单数据
  df_raw = pd.read_excel(uploaded_file, sheet_name=0)

  # 定位交易数据区（UOB 导出格式通常从第 8 行起）
  tx_df = df_raw.iloc[5:].copy()
  tx_df.columns = ['Date_Raw', 'Description', 'Withdrawal', 'Deposit', 'Balance']

  # 清洗数字和日期类型
  tx_df['Withdrawal'] = pd.to_numeric(tx_df['Withdrawal'], errors='coerce').fillna(0)
  tx_df['Deposit'] = pd.to_numeric(tx_df['Deposit'], errors='coerce').fillna(0)
  tx_df['Balance'] = pd.to_numeric(tx_df['Balance'], errors='coerce')
  tx_df['Date'] = pd.to_datetime(tx_df['Date_Raw'], errors='coerce')
  tx_df = tx_df.dropna(subset=['Date'])

  # 3. 精确倒推月初（1号）开盘余额
  # 读取交易数据区最深处（最古老）的一笔记录
  oldest_row = tx_df.iloc[-1]
  oldest_bal = oldest_row['Balance']
  oldest_w = oldest_row['Withdrawal']
  oldest_d = oldest_row['Deposit']

  # 1号期初余额 = 最古老交易余额 - 存款 + 取款
  start_of_month_bal = oldest_bal - oldest_d + oldest_w

  # 4. 获取月份信息并构建当月全量日期序列
  max_date = tx_df['Date'].max()
  year = max_date.year
  month = max_date.month
  num_days = calendar.monthrange(year, month)[1]

  # 按日期汇总每日提款与存款
  daily_summary = tx_df.groupby(tx_df['Date'].dt.date)[['Withdrawal', 'Deposit']].sum().to_dict('index')

  # 5. 循环构建全月 1 日至 30/31 日的数据表
  records = []
  cur_bal = start_of_month_bal

  for d in range(1, num_days + 1):
   date_obj = datetime.date(year, month, d)
   w = daily_summary.get(date_obj, {}).get('Withdrawal', 0.0)
   p = daily_summary.get(date_obj, {}).get('Deposit', 0.0)
   cur_bal = cur_bal - w + p

   records.append({
    "Date": date_obj.strftime("%Y-%m-%d"),
    "Withdraw": float(w),
    "Deposit": float(p),
    "Balance": float(cur_bal)
   })

  full_month_df = pd.DataFrame(records)

  st.success(f"账单解析成功！月份：{year}-{month:02d} | 倒推 1 日期初余额：SGD {start_of_month_bal:,.2f}")

  # 6. 可编辑数据表格与交互测算
  st.subheader("📊 全月数据与模拟测算")
  st.info("💡 可以在下表的【Withdraw】和【Deposit】列中双击修改数值，系统会自动实时重新计算【模拟余额】及顶部【日均余额】。")

  edited_df = st.data_editor(
   full_month_df,
   column_config={
    "Date": st.column_config.TextColumn("Date", disabled=True),
    "Withdraw": st.column_config.NumberColumn("Withdraw (支出)", format="%.2f"),
    "Deposit": st.column_config.NumberColumn("Deposit (收入)", format="%.2f"),
    "Balance": st.column_config.NumberColumn("Balance (账单实际)", format="%.2f", disabled=True)
   },
   disabled=["Date", "Balance"],
   hide_index=True,
   num_rows="fixed",
   use_container_width=True
  )

  # 7. 实时计算模拟余额列与汇总统计
  simulated_bals = []
  sim_cur = start_of_month_bal

  for idx, row in edited_df.iterrows():
   sim_cur = sim_cur - row['Withdraw'] + row['Deposit']
   simulated_bals.append(sim_cur)

  edited_df['Simulated_Balance'] = simulated_bals

  total_sim_bal = sum(simulated_bals)
  avg_sim_bal = total_sim_bal / num_days

  # 8. 关键 KPI 指标卡展示
  col1, col2, col3 = st.columns(3)
  col1.metric("当月总天数 (# of days)", f"{num_days} 天")
  col2.metric("累计余额 (Total balance)", f"SGD {total_sim_bal:,.2f}")
  col3.metric("测算日均余额 (Daily balance)", f"SGD {avg_sim_bal:,.2f}")

  # 9. 结果导出功能
  csv = edited_df.to_csv(index=False).encode('utf-8-sig')
  st.download_button(
   label="📥 导出测算结果为 CSV 文件",
   data=csv,
   file_name=f"DAB_Simulation_{year}_{month:02d}.csv",
   mime="text/csv"
  )

 except Exception as e:
  st.error(f"解析账单文件时发生错误，请检查上传的文件格式：{e}")
