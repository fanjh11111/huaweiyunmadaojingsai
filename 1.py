import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import confusion_matrix

print("=== 开始执行 1.py ===")

# 设备
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# LSTM 模型
class TimeSeriesClassifier(nn.Module):
    def __init__(self, input_size=320, hidden_size=256, num_classes=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out

# 读取数据
print("\n1. 开始读取数据...")
try:
    df = pd.read_excel(r"D:\项目2\hangkong_3D\hangkong_3D\直升机发动机传感器数据_标签化.xlsx")
    print(f"数据读取成功，形状: {df.shape}")
    print(f"数据列数: {len(df.columns)}")

    # 显示列名
    print("\n=== 数据列名 ===")
    columns = df.columns.tolist()
    for i, col in enumerate(columns):
        print(f"{i}: {col}")
except Exception as e:
    print(f"读取数据时出错: {e}")
    exit(1)

# 准备数据
print("\n2. 准备数据...")
try:
    X = df.iloc[:, 1:321].values
    y = df.iloc[:, -1].values

    # 获取实际的特征名称（列名）
    feature_names = df.columns[1:321].tolist()
    print(f"X形状: {X.shape}, y形状: {y.shape}")
    print(f"特征名称示例: {feature_names[:5]}...")
except Exception as e:
    print(f"准备数据时出错: {e}")
    exit(1)

# 归一化
print("\n3. 开始归一化数据...")
try:
    scaler = MinMaxScaler()
    X = scaler.fit_transform(X)
    print("归一化完成")
except Exception as e:
    print(f"归一化时出错: {e}")
    exit(1)

# 构造时间序列
print("\n4. 开始构造时间序列...")
try:
    def make_data(X, y, seq_len=20):
        data_X, data_y = [], []
        for i in range(len(X) - seq_len):
            data_X.append(X[i:i+seq_len])
            data_y.append(y[i+seq_len])
        return np.array(data_X), np.array(data_y)

    step = 20
    X_seq, y_seq = make_data(X, y, seq_len=step)
    print(f"时间序列构造完成，形状: {X_seq.shape}, {y_seq.shape}")
except Exception as e:
    print(f"构造时间序列时出错: {e}")
    exit(1)

# 转张量
print("\n5. 转换为张量...")
try:
    X_tensor = torch.tensor(X_seq, dtype=torch.float32).to(device)
    y_tensor = torch.tensor(y_seq, dtype=torch.long).to(device)
    dataset = TensorDataset(X_tensor, y_tensor)
    loader = DataLoader(dataset, batch_size=64, shuffle=False)
    print(f"张量转换完成，批次数量: {len(loader)}")
except Exception as e:
    print(f"转换张量时出错: {e}")
    exit(1)

# 模型
print("\n6. 初始化模型...")
try:
    model = TimeSeriesClassifier().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    print("模型初始化完成")
except Exception as e:
    print(f"初始化模型时出错: {e}")
    exit(1)

# 训练
print("\n7. 开始训练...")
try:
    epochs = 15
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        batch_count = 0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            out = model(batch_x)
            loss = criterion(out, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            batch_count += 1
        print(f"第 {epoch+1} 轮 | 损失: {total_loss:.4f}")
    print("训练完成")
except Exception as e:
    print(f"训练时出错: {e}")
    exit(1)

# 预测
print("\n8. 开始预测...")
try:
    model.eval()
    all_pred = []
    all_true = []

    with torch.no_grad():
        for batch_x, batch_y in loader:
            out = model(batch_x)
            pred = out.argmax(dim=1)
            all_pred.extend(pred.cpu().numpy())
            all_true.extend(batch_y.cpu().numpy())

    all_pred = np.array(all_pred)
    all_true = np.array(all_true)
    print(f"预测完成，样本数: {len(all_pred)}")
except Exception as e:
    print(f"预测时出错: {e}")
    exit(1)

# 计算准确率
print("\n9. 计算模型效果...")
try:
    acc = np.mean(all_pred == all_true)
    cm = confusion_matrix(all_true, all_pred)

    print("="*50)
    print("✅ 训练完成！模型效果：")
    print(f"准确率: {acc:.4f}")
    print("混淆矩阵:")
    print(cm)
    print("="*50)
except Exception as e:
    print(f"计算模型效果时出错: {e}")
    exit(1)

# 合并连续故障段
print("\n10. 合并连续故障段...")
try:
    def get_continuous_faults(preds):
        segments = []
        start = None
        for i, val in enumerate(preds):
            if val == 1:
                if start is None:
                    start = i
            else:
                if start is not None:
                    segments.append((start, i-1))
                    start = None
        if start is not None:
            segments.append((start, len(preds)-1))
        return segments

    fault_segments = get_continuous_faults(all_pred)
    print(f"✅ 共识别出 {len(fault_segments)} 段连续故障")
except Exception as e:
    print(f"合并故障段时出错: {e}")
    exit(1)

# 输出前 30 段故障
print("\n11. 分析故障段...")
try:
    top_k = 30
    show_segments = fault_segments[:top_k]

    result = []
    for idx, (s, e) in enumerate(show_segments, 1):
        length = e - s + 1

        # 取这段故障的所有样本，计算共同关键特征
        seq_list = []
        for i in range(s, e+1):
            if i < len(X_seq):
                seq_list.append(X_seq[i])
        seq_mat = np.array(seq_list)
        mean_seq = seq_mat.mean(axis=(0,1))
        std_seq = seq_mat.mean(axis=0).std(axis=0)
        score = np.abs(mean_seq) * std_seq
        top10 = np.argsort(score)[::-1][:10]
        # 使用真实的特征名称
        top_features = [feature_names[i] for i in top10]

        result.append({
            "故障段": idx,
            "起始样本": s,
            "结束样本": e,
            "持续长度": length,
            "Top10关键特征": ", ".join(top_features)
        })
        print(f"故障段 {idx}: 起始{s}, 结束{e}, 长度{length}")
        print(f"  关键特征: {', '.join(top_features)}")

    print(f"故障段分析完成，生成 {len(result)} 条结果")
except Exception as e:
    print(f"分析故障段时出错: {e}")
    exit(1)

# 打印输出
print("\n12. 打印故障段详情...")
try:
    print("="*90)
    print(f"📊 前 {top_k} 段连续故障详情")
    print("="*90)
    for item in result:
        print(f"第{item['故障段']:2d}段 | 起始:{item['起始样本']:4d} | 结束:{item['结束样本']:4d} | 长度:{item['持续长度']:3d}")
        print(f"关键特征：{item['Top10关键特征']}")
        print("-"*90)
except Exception as e:
    print(f"打印故障段时出错: {e}")
    exit(1)

# 保存CSV
print("\n13. 保存结果...")
try:
    df_out = pd.DataFrame(result)
    df_out.to_csv(r"连续故障段分析报告.csv", index=False, encoding='utf-8-sig')
    print("✅ 文件已保存：连续故障段分析报告.csv")
except Exception as e:
    print(f"保存结果时出错: {e}")
    exit(1)

print("\n=== 1.py 执行完成 ===")