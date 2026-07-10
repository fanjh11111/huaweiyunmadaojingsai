import pandas as pd

df = pd.read_excel(r"D:\项目2\hangkong_3D\hangkong_3D\直升机发动机传感器数据_标签化.xlsx")

with open('columns_output.txt', 'w', encoding='utf-8') as f:
    f.write(f"数据形状: {df.shape}\n")
    f.write(f"数据列数: {len(df.columns)}\n\n")

    columns = df.columns.tolist()
    for i, col in enumerate(columns):
        f.write(f"{i}: {col}\n")

print("列名已保存到columns_output.txt")