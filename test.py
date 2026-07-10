import pandas as pd

print("测试Python环境...")
print(f"pandas版本: {pd.__version__}")

print("\n尝试读取Excel文件...")
try:
    df = pd.read_excel(r"D:\项目2\hangkong_3D\hangkong_3D\直升机发动机传感器数据_标签化.xlsx")
    print(f"数据读取成功！")
    print(f"数据形状: {df.shape}")
    print(f"前5行数据:")
    print(df.head())
except Exception as e:
    print(f"读取失败: {e}")

print("\n测试完成！")