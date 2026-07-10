import pandas as pd
import json

df = pd.read_excel(r"D:\项目2\hangkong_3D\hangkong_3D\直升机发动机传感器数据_标签化.xlsx")

columns = df.columns.tolist()

with open('feature_names.json', 'w', encoding='utf-8') as f:
    json.dump(columns, f, ensure_ascii=False, indent=2)

print("特征名称已保存到feature_names.json")
print(f"共有 {len(columns)} 列")