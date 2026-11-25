# -*- coding: utf-8 -*-
"""LEAR 轻量可训练网络

T-CNN  教学语义类型分类网络：块文本 → {definition, theorem, example, proof, note, body}
E-BiLSTM 句级蕴含判定网络：(claim, evidence句) → supported / unsupported

设计约束：参数量小（CPU 可训练、推理毫秒级），与规则骨架互补。
"""
from __future__ import annotations

import re
import json
import math
from pathlib import Path

import torch
import torch.nn as nn

LABELS = ["definition", "theorem", "example", "proof", "note", "body"]
_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]+|[A-Za-z0-9_.]+")


def simple_tokenize(text: str) -> list[str]:
    """中文按字二元+英文数字词，无需外部词典，训推一致"""
    toks = []
    for seg in _TOKEN_RE.findall(text or ""):
        if re.fullmatch(r"[\u4e00-\u9fff]+", seg):
            toks.extend([seg[i:i + 2] for i in range(max(1, len(seg) - 1))] or [seg])
        else:
            toks.append(seg.lower())
    return toks


class Vocab:
    def __init__(self, min_freq: int = 1, max_size: int = 20000):
        self.min_freq, self.max_size = min_freq, max_size
        self.itos = ["<pad>", "<unk>"]
        self.stoi = {w: i for i, w in enumerate(self.itos)}

    def fit(self, texts: list[str]) -> "Vocab":
        from collections import Counter
        cnt = Counter()
        for t in texts:
            cnt.update(simple_tokenize(t))
        for w, c in cnt.most_common(self.max_size):
            if c >= self.min_freq and w not in self.stoi:
                self.stoi[w] = len(self.itos)
                self.itos.append(w)
        return self

    def encode(self, text: str, max_len: int = 64) -> list[int]:
        ids = [self.stoi.get(w, 1) for w in simple_tokenize(text)[:max_len]]
        return ids + [0] * (max_len - len(ids))

    def save(self, path: str):
        Path(path).write_text(json.dumps({"itos": self.itos}, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str) -> "Vocab":
        v = cls()
        v.itos = json.loads(Path(path).read_text(encoding="utf-8"))["itos"]
        v.stoi = {w: i for i, w in enumerate(v.itos)}
        return v


class TCNN(nn.Module):
    """TextCNN 教学语义类型分类：多粒度卷积 + 最大时序池化"""

    def __init__(self, vocab_size: int, n_classes: int = 6, embed_dim: int = 128,
                 kernels=(2, 3, 4), n_filters: int = 64, dropout: float = 0.2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.convs = nn.ModuleList(
            nn.Conv1d(embed_dim, n_filters, k, padding=k // 2) for k in kernels)
        self.fc = nn.Linear(n_filters * len(kernels), n_classes)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        e = self.embed(x).transpose(1, 2)              # (B, D, L)
        feats = [torch.relu(conv(e)).max(dim=2).values for conv in self.convs]
        return self.fc(self.dropout(torch.cat(feats, dim=1)))


class EBiLSTM(nn.Module):
    """句级蕴含判定：共享嵌入 + BiLSTM + 交互特征 [u; v; |u-v|; u*v] + MLP"""

    def __init__(self, vocab_size: int, embed_dim: int = 128, hidden: int = 64,
                 n_classes: int = 2, dropout: float = 0.2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden, batch_first=True,
                            bidirectional=True, num_layers=1)
        self.mlp = nn.Sequential(
            nn.Linear(hidden * 2 * 4, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, n_classes))

    def _encode(self, x):
        e = self.embed(x)
        out, (h, _) = self.lstm(e)
        return torch.cat([h[-2], h[-1]], dim=1)        # (B, 2H)

    def forward(self, x1, x2):
        u, v = self._encode(x1), self._encode(x2)
        feats = torch.cat([u, v, torch.abs(u - v), u * v], dim=1)
        return self.mlp(feats)


def train_epoch(model, loader, optimizer, device):
    model.train()
    total_loss, correct, n = 0.0, 0, 0
    crit = nn.CrossEntropyLoss()
    for batch in loader:
        optimizer.zero_grad()
        if len(batch) == 3:                     # (x1, x2, y) 蕴含任务
            x1, x2, y = [b.to(device) for b in batch]
            logits = model(x1, x2)
        else:                                   # (x, y) 分类任务
            x, y = [b.to(device) for b in batch]
            logits = model(x)
        loss = crit(logits, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * y.size(0)
        correct += (logits.argmax(1) == y).sum().item()
        n += y.size(0)
    return total_loss / max(n, 1), correct / max(n, 1)


@torch.no_grad()
def evaluate(model, loader, device, n_classes: int = 2):
    model.eval()
    crit = nn.CrossEntropyLoss()
    total_loss, n = 0.0, 0
    correct = 0
    tp = fp = tn = fn = 0
    for batch in loader:
        if len(batch) == 3:
            x1, x2, y = [b.to(device) for b in batch]
            logits = model(x1, x2)
        else:
            x, y = [b.to(device) for b in batch]
            logits = model(x)
        total_loss += crit(logits, y).item() * y.size(0)
        n += y.size(0)
        pred = logits.argmax(1).cpu().tolist()
        gold = y.cpu().tolist()
        correct += sum(1 for p, g in zip(pred, gold) if p == g)
        if n_classes == 2:
            for p, g in zip(pred, gold):
                if p == 1 and g == 1:
                    tp += 1
                elif p == 1 and g == 0:
                    fp += 1
                elif p == 0 and g == 0:
                    tn += 1
                else:
                    fn += 1
    out = {"loss": total_loss / max(n, 1), "acc": round(correct / max(n, 1), 4)}
    if n_classes == 2:
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        out.update({"P": round(prec, 4), "R": round(rec, 4),
                    "F1": round(2 * prec * rec / (prec + rec), 4) if prec + rec else 0.0})
    return out
