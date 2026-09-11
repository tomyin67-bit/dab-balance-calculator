# 银行月度日均余额 (DAB) 测算工具

上传银行导出的 Excel 交易流水（UOB 格式），自动推算全月每日余额并支持在线模拟测算日均余额。

## 使用
1. 在网页中上传 `.xls` / `.xlsx` 账单文件
2. 系统自动解析并倒推 1 日期初余额，生成全月每日余额表
3. 可在 `Withdraw` / `Deposit` 列直接修改数值做模拟
4. 顶部显示当月天数、累计余额、测算日均余额
5. 可导出测算结果为 CSV

## 本地运行
```
pip install -r requirements.txt
streamlit run app.py
```

## 部署
- Streamlit Community Cloud: 连接本仓库即可一键部署（需 GitHub 账号）
- Hugging Face Spaces: 选择 Streamlit SDK，上传本仓库内容
