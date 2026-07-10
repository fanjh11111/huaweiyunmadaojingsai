import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import confusion_matrix

# 设备
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using", device)

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

# 读取数据（Excel）
df = pd.read_excel(r"D:\项目2\hangkong_3D\hangkong_3D\直升机发动机传感器数据_标签化.xlsx")
X = df.iloc[:, 1:321].values
y = df.iloc[:, -1].values

# ====================== 修复：标签字符串转数字 0/1 ======================
y = pd.Series(y).astype(str).map({'正常':0, '故障':1, '0':0, '1':1}).values
# 兜底：无法识别的填0
y = np.nan_to_num(y, nan=0).astype(int)

feature_names = [f"第{i}列数据" for i in range(1, 321)]

# 归一化
scaler = MinMaxScaler()
X = scaler.fit_transform(X)

# 构造时间序列
def make_data(X, y, seq_len=20):
    data_X, data_y = [], []
    for i in range(len(X) - seq_len):
        data_X.append(X[i:i+seq_len])
        data_y.append(y[i+seq_len])
    return np.array(data_X), np.array(data_y)

step = 20
X_seq, y_seq = make_data(X, y, seq_len=step)

# 转张量
X_tensor = torch.tensor(X_seq, dtype=torch.float32).to(device)
y_tensor = torch.tensor(y_seq, dtype=torch.long).to(device)
dataset = TensorDataset(X_tensor, y_tensor)
loader = DataLoader(dataset, batch_size=64, shuffle=False)

# 模型
model = TimeSeriesClassifier().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 训练
print("\n开始训练...")
epochs = 15
for epoch in range(epochs):
    model.train()
    total_loss = 0
    for batch_x, batch_y in loader:
        optimizer.zero_grad()
        out = model(batch_x)
        loss = criterion(out, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"第 {epoch+1} 轮 | 损失: {total_loss:.4f}")

# ====================== 预测 + 准确率 + 混淆矩阵 ======================
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

# 计算准确率
acc = np.mean(all_pred == all_true)
cm = confusion_matrix(all_true, all_pred)

print("\n" + "="*50)
print("✅ 训练完成！模型效果：")
print(f"准确率: {acc:.4f}")
print("混淆矩阵:")
print(cm)
print("="*50)

# ====================== 核心：合并连续故障段 ======================
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
print(f"\n✅ 共识别出 {len(fault_segments)} 段连续故障")

# ====================== 输出前 30 段故障 ======================
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
    top_features = [feature_names[i] for i in top10]

    result.append({
        "故障段": idx,
        "起始样本": s,
        "结束样本": e,
        "持续长度": length,
        "Top10关键特征": ", ".join(top_features)
    })

# ====================== 打印输出 ======================
print("\n" + "="*90)
print(f"📊 前 {top_k} 段连续故障详情")
print("="*90)
for item in result:
    print(f"第{item['故障段']:2d}段 | 起始:{item['起始样本']:4d} | 结束:{item['结束样本']:4d} | 长度:{item['持续长度']:3d}")
    print(f"关键特征：{item['Top10关键特征']}")
    print("-"*90)

# ====================== 保存CSV ======================
df_out = pd.DataFrame(result)
df_out.to_csv(r"D:\项目2\hangkong_3D\hangkong_3D\连续故障段分析报告.csv", index=False, encoding='utf-8-sig')

print("\n✅ 文件已保存：连续故障段分析报告.csv")