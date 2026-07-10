import pandas as pd
import os

# 👉 请将这里的路径替换为你电脑上该文件的真实绝对路径
# Windows 路径前面最好加 'r' 防止转义，例如 r"D:\data\直升机发动机传感器数据_标签化.xlsx"
FILE_PATH = r"C:\Users\fanjihan\Desktop\STUDY\26BiSaiYong\hangkong_3D\data.xlsx"

def check_data_file(file_path):
    print(f"开始侦测文件: {file_path}\n" + "="*40)

    if not os.path.exists(file_path):
        print("❌ 错误：找不到文件，请检查绝对路径是否拼写正确！")
        return

    df = None

    # 策略 1: 当做纯文本 CSV 读取 (尝试 UTF-8)
    try:
        print("⏳ 尝试 1: 以纯文本 CSV 格式 (UTF-8) 读取...")
        df = pd.read_csv(file_path, encoding='utf-8')
        print("✅ 成功！这是一个 UTF-8 编码的 CSV 文件。")
    except Exception as e1:
        # 策略 2: 当做纯文本 CSV 读取 (尝试 GBK - Windows 常见)
        try:
            print(f"   [失败] {e1}\n⏳ 尝试 2: 以纯文本 CSV 格式 (GBK) 读取...")
            df = pd.read_csv(file_path, encoding='gbk')
            print("✅ 成功！这是一个 GBK 编码的 CSV 文件。")
        except Exception as e2:
            # 策略 3: 当做真正的二进制 Excel (.xlsx) 读取
            try:
                print(f"   [失败] {e2}\n⏳ 尝试 3: 以纯正 Excel 二进制格式读取...")
                df = pd.read_excel(file_path)
                print("✅ 成功！这是一个真正的 Excel 文件。")
            except Exception as e3:
                print(f"   [失败] {e3}")
                print("\n💥 彻底失败：Python 也无法读取此文件。文件极大概率已损坏，或处于被其他软件独占锁定的状态。")
                return

    # 如果成功读取，打印核心信息
    if df is not None:
        print("\n📊 【文件解析报告】")
        print(f"总行数: {len(df)}")
        print(f"总列数: {len(df.columns)}")

        print("\n🔍 【提取到的真实列名 (前20个)】:")
        columns_list = df.columns.tolist()
        for i, col in enumerate(columns_list[:20]):
            # 打印列名时，顺便带上它的类型和长度，看看有没有隐藏空格
            print(f"  [{i+1}] '{col}' (长度: {len(str(col))})")
        if len(columns_list) > 20:
            print(f"  ... 以及其他 {len(columns_list) - 20} 列")

        print("\n📝 【前 2 行数据预览】:")
        print(df.head(2).to_string())

if __name__ == "__main__":
    check_data_file(FILE_PATH)