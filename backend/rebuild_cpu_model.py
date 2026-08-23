"""在 CPU 环境下重建 LSTM 模型并重新 trace，生成可在本机运行的 TorchScript 文件。

原 lstm_engine_traced.pt 是在 CUDA 上 trace 的，内部 zeros 初始化被固化成
device='cuda:0'，在纯 CPU 机器上调用会报
"Could not run 'aten::empty.memory_format' with arguments from the 'CUDA' backend"。

本脚本：
1. 依据 1.py 中的 TimeSeriesClassifier 定义重建模型；
2. 从 lstm_engine_weights.pth 载入权重；
3. 在 CPU 上用示例输入重新 trace；
4. 输出 lstm_engine_traced_cpu.pt（不覆盖原始 GPU 文件，方便回退）。
"""
import copy
import torch
import torch.nn as nn


class TimeSeriesClassifier(nn.Module):
    def __init__(self, input_size=320, hidden_size=256, num_classes=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out


def main():
    device = torch.device("cpu")
    model = TimeSeriesClassifier().to(device)
    sd = torch.load("lstm_engine_weights.pth", map_location=device, weights_only=False)
    model.load_state_dict(sd)
    model.eval()

    # 示例输入：(batch, seq_len, input_size) = (1, 20, 320)
    example = torch.randn(1, 20, 320, dtype=torch.float32, device=device)
    with torch.no_grad():
        traced = torch.jit.trace(model, example)

    # 自测：确保 trace 后可在 CPU 正常推理
    with torch.no_grad():
        out = traced(example)
    assert out.shape == (1, 2), f"unexpected output shape {tuple(out.shape)}"

    torch.jit.save(traced, "lstm_engine_traced_cpu.pt")
    print("saved lstm_engine_traced_cpu.pt, sample out:", out[0].tolist())


if __name__ == "__main__":
    main()
