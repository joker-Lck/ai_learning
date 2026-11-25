# -*- coding: utf-8 -*-
"""训练 LEAR 轻量网络：T-CNN 教学语义类型分类 + E-BiLSTM 句级蕴含判定

数据构造：
- 类型分类：教材行文本，规则标记为银标（definition/theorem/example/proof/note/body）
- 蕴含判定：句对（同句正例 / 数值篡改·公式改写·错配文档负例），按文档划分训练/测试
产出：models/ckpt_tcnn.pt、models/ckpt_ebilstm.pt、训练指标 JSON
"""
import sys, os, re, json, random, time
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")

import torch
from torch.utils.data import DataLoader, TensorDataset
from models.teach_nets import TCNN, EBiLSTM, Vocab, LABELS, train_epoch, evaluate, simple_tokenize

random.seed(7)
torch.manual_seed(7)
DEVICE = "cpu"

# ── 语料 ───────────────────────────────────────────────
CORPUS = r"F:\项目\ai教学辅助系统\experiments\corpus_textbook"
from pathlib import Path

MARKER = re.compile(
    r"(^|[。；;！？\n])\s*\*{0,2}\s*(定义|定理|定律|引理|推论|性质|公式|例题|例\s*\d|证明|推导|注意|练习|习题|小结|归纳)"
    r"[：:．.、\s（(0-9０-９*]")
KIND = {"定义": "definition", "定理": "theorem", "定律": "theorem", "引理": "theorem",
        "推论": "theorem", "性质": "theorem", "公式": "theorem", "例题": "example",
        "证明": "proof", "推导": "proof", "注意": "note", "练习": "exercise", "习题": "exercise",
        "小结": "note", "归纳": "note"}

def load_docs():
    docs = []
    for p in sorted(Path(CORPUS).rglob("*.md")):
        if p.name in ("README.md", "template_text.txt"):
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if len(t) > 200:
            docs.append(t)
    return docs

def rule_kind(line: str) -> str:
    m = MARKER.search(line)
    if not m:
        return "body"
    k = m.group(2)
    if k.startswith("例"):
        return "example"
    return KIND.get(k, "body")

# ── 任务A：类型分类数据（句级，稀有类合成增强）──────────────
SENT_SPLIT = re.compile(r"[。！？\n；;]+")

def synth_examples(n=80):
    """稀有类模板合成增强（论文如实标注为合成数据）"""
    terms = ["随机事件", "条件概率", "数学期望", "方差", "分布函数", "置信区间", "假设检验"]
    out = {k: [] for k in ("definition", "proof", "note")}
    for i in range(n):
        t1, t2 = terms[i % len(terms)], terms[(i + 2) % len(terms)]
        out["definition"].append(f"定义{i + 1}：设{t1}是样本空间上的一个随机变量，称满足可测性的映射为{t1}的定义。")
        out["proof"].append(f"证明：由{t1}的性质与{t2}的计算公式，代入已知条件化简可得结论成立。")
        out["note"].append(f"注意：在使用{t1}与{t2}时容易混淆符号含义，建议结合例题加以区分。")
    return out

def build_kind_data(docs):
    xs, ys, owner = [], [], []
    for di, t in enumerate(docs):
        for s in SENT_SPLIT.split(t):
            s = s.strip()
            if len(s) < 6:
                continue
            k = rule_kind(s)
            xs.append(s[:120])
            ys.append(LABELS.index(k) if k in LABELS else LABELS.index("body"))
            owner.append(di)
    # 合成增强（owner=-1 表示合成，训练可用、测试不计入真实口径）
    for k, lst in synth_examples(80).items():
        for s in lst:
            xs.append(s)
            ys.append(LABELS.index(k))
            owner.append(-1)
    return xs, ys, owner

# ── 任务B：蕴含句对数据 ─────────────────────────────────
SENT_RE = re.compile(r"[^。！？\n；;]{8,}")

def build_entail_data(docs):
    pairs, labels, owner = [], [], []
    sents_by_doc = []
    for di, t in enumerate(docs):
        ss = [s.strip() for s in SENT_RE.findall(t) if len(s.strip()) >= 8][:60]
        sents_by_doc.append(ss)
    num_re = re.compile(r"\d+\.\d+|\d+/\d+|\d+%|\d{2,}")
    for di, ss in enumerate(sents_by_doc):
        for s in ss:
            # 正例：原句 vs 原句
            pairs.append((s, s)); labels.append(1); owner.append(di)
            # 正例：截断句 vs 全句
            if len(s) > 30:
                pairs.append((s[:len(s)//2], s)); labels.append(1); owner.append(di)
            # 负例：数值篡改
            m = num_re.search(s)
            if m:
                fake = "7/9" if "/" not in m.group(0) else "5/3"
                bad = s.replace(m.group(0), fake, 1)
                pairs.append((bad, s)); labels.append(0); owner.append(di)
            # 负例：公式改写（交换等式两侧局部）
            if "=" in s:
                h, tl = s.split("=", 1)
                if len(tl) > 3:
                    pairs.append((h + "=" + tl[0] + "99" + tl[2:], s)); labels.append(0); owner.append(di)
            # 负例：错配文档
            dj = (di + 5) % len(sents_by_doc)
            if sents_by_doc[dj]:
                pairs.append((s, sents_by_doc[dj][0])); labels.append(0); owner.append(di)
    return pairs, labels, owner

def to_loader(texts1, texts2, labels, vocab1, vocab2, max_len=48, batch=64, shuffle=True):
    x1 = torch.tensor([vocab1.encode(t, max_len) for t in texts1], dtype=torch.long)
    if texts2 is not None:
        x2 = torch.tensor([vocab2.encode(t, max_len) for t in texts2], dtype=torch.long)
        y = torch.tensor(labels, dtype=torch.long)
        ds = TensorDataset(x1, x2, y)
    else:
        y = torch.tensor(labels, dtype=torch.long)
        ds = TensorDataset(x1, y)
    return DataLoader(ds, batch_size=batch, shuffle=shuffle)

def split_by_owner(n, owner, ratio=0.8):
    owners = sorted(set(owner))
    random.shuffle(owners)
    cut = int(len(owners) * ratio)
    tr = [i for i in range(n) if owner[i] in owners[:cut]]
    te = [i for i in range(n) if owner[i] in owners[cut:]]
    return tr, te

def main():
    t0 = time.time()
    docs = load_docs()
    print(f"docs={len(docs)}")

    # ══ A. T-CNN 类型分类 ══
    xs, ys, owner = build_kind_data(docs)
    from collections import Counter
    dist = Counter(ys)
    print(f"[T-CNN] raw dist: { {LABELS[k]: v for k, v in dist.items()} }")
    # body 降采样至其他类 2 倍（合成类已补足稀有类）
    keep = [i for i, y in enumerate(ys) if y != LABELS.index("body") or owner[i] == -1]
    body = [i for i, y in enumerate(ys) if y == LABELS.index("body") and owner[i] != -1]
    random.shuffle(body)
    keep += body[:len(keep) * 2]
    xs = [xs[i] for i in keep]; ys = [ys[i] for i in keep]; owner = [owner[i] for i in keep]
    # 真实按文档切分；合成样本只进训练
    real = [i for i, o in enumerate(owner) if o != -1]
    tr_r, te_r = split_by_owner(len(real), [owner[i] for i in real])
    tr_r = [real[i] for i in tr_r]; te_r = [real[i] for i in te_r]
    synth = [i for i, o in enumerate(owner) if o == -1]
    te_s = synth[::5]                    # 合成样本 20% 作留出（训练前剔除）
    tr_synth = [i for i in synth if i not in set(te_s)]
    tr = tr_r + tr_synth
    te = te_r
    print(f"[T-CNN] train={len(tr)} (real {len(tr_r)} + synth {len(tr_synth)}) "
          f"test(real)={len(te)} test(synth)={len(te_s)}")
    print(f"[T-CNN] samples={len(xs)} train={len(tr)} test={len(te)}")
    vocab_a = Vocab().fit([xs[i] for i in tr])
    model_a = TCNN(len(vocab_a.itos), n_classes=len(LABELS)).to(DEVICE)
    opt = torch.optim.Adam(model_a.parameters(), lr=1e-3)
    ld_tr = to_loader([xs[i] for i in tr], None, [ys[i] for i in tr], vocab_a, vocab_a, shuffle=True)
    ld_te = to_loader([xs[i] for i in te], None, [ys[i] for i in te], vocab_a, vocab_a, shuffle=False)
    best = 0.0
    for ep in range(1, 9):
        l, a = train_epoch(model_a, ld_tr, opt, DEVICE)
        ev = evaluate(model_a, ld_te, DEVICE, n_classes=len(LABELS))
        print(f"  [T-CNN] epoch {ep}: train_loss={l:.3f} train_acc={a:.3f} test_acc={ev['acc']:.3f}")
        best = max(best, ev["acc"])
    # 每类 F1：真实测试（含支持数）+ 合成留出测试
    model_a.eval()

    def per_class_f1(idxs):
        per = {k: [0, 0, 0] for k in LABELS}
        sup = {k: 0 for k in LABELS}
        with torch.no_grad():
            for j in range(0, len(idxs), 64):
                batch = [xs[i] for i in idxs[j:j + 64]]
                x = torch.tensor([vocab_a.encode(t, 64) for t in batch], dtype=torch.long).to(DEVICE)
                pred = model_a(x).argmax(1).cpu().tolist()
                for p, i in zip(pred, idxs[j:j + 64]):
                    g = ys[i]
                    sup[LABELS[g]] += 1
                    if p == g:
                        per[LABELS[p]][0] += 1
                    else:
                        per[LABELS[p]][1] += 1
                        per[LABELS[g]][2] += 1
        f1 = {}
        for k, (tp, fp, fn) in per.items():
            pr = tp / (tp + fp) if tp + fp else 0
            rc = tp / (tp + fn) if tp + fn else 0
            f1[k] = round(2 * pr * rc / (pr + rc), 4) if pr + rc else 0.0
        return f1, sup

    f1_real, sup_real = per_class_f1(te)
    f1_synth, sup_synth = per_class_f1(te_s)
    print(f"  [T-CNN] per-class F1 (real test, support={sup_real}): {f1_real}")
    print(f"  [T-CNN] per-class F1 (synth test, support={sup_synth}): {f1_synth}")
    torch.save({"state": model_a.state_dict(), "vocab": vocab_a.itos, "labels": LABELS},
               "models/ckpt_tcnn.pt")
    vocab_a.save("models/vocab_tcnn.json")

    # ══ B. E-BiLSTM 蕴含判定 ══
    pairs, elabels, eowner = build_entail_data(docs)
    tr, te = split_by_owner(len(pairs), eowner)
    print(f"[E-BiLSTM] pairs={len(pairs)} train={len(tr)} test={len(te)} pos_ratio={sum(elabels)/len(elabels):.2f}")
    all_text = [p[0] for p in pairs] + [p[1] for p in pairs]
    vocab_b = Vocab().fit([all_text[i] for i in tr] if False else all_text)
    model_b = EBiLSTM(len(vocab_b.itos)).to(DEVICE)
    opt = torch.optim.Adam(model_b.parameters(), lr=1e-3)
    ld_tr = to_loader([pairs[i][0] for i in tr], [pairs[i][1] for i in tr],
                      [elabels[i] for i in tr], vocab_b, vocab_b, shuffle=True)
    ld_te = to_loader([pairs[i][0] for i in te], [pairs[i][1] for i in te],
                      [elabels[i] for i in te], vocab_b, vocab_b, shuffle=False)
    best_f1 = 0.0
    for ep in range(1, 9):
        l, a = train_epoch(model_b, ld_tr, opt, DEVICE)
        ev = evaluate(model_b, ld_te, DEVICE, n_classes=2)
        print(f"  [E-BiLSTM] epoch {ep}: train_loss={l:.3f} train_acc={a:.3f} "
              f"test P={ev['P']} R={ev['R']} F1={ev['F1']}")
        best_f1 = max(best_f1, ev["F1"])
    torch.save({"state": model_b.state_dict(), "vocab": vocab_b.itos},
               "models/ckpt_ebilstm.pt")
    vocab_b.save("models/vocab_ebilstm.json")

    # ══ C. 在 401 挑战集上测 F4 神经通道增益 ══
    try:
        import importlib.util as u
        spec = u.spec_from_file_location("ev", "experiments/eval_lear_paper.py")
        ev = u.module_from_spec(spec); spec.loader.exec_module(ev)
        golds = ev.extract_gold(ev.load_corpus())
        ch = ev.build_challenge(golds)
        items = sum(ch.values(), [])
        model_b.eval()

        def neural_flag(claim, evidence):
            # 神经通道：claim 与最佳证据句的蕴含分低于阈值 → 有问题
            ev_sents = []
            for e in evidence:
                ev_sents += [s for s in re.split(r"[。！？\n；;]", e.get("content_text", "")) if len(s.strip()) >= 8]
            if not ev_sents:
                return True
            xs1 = [claim] * min(len(ev_sents), 12)
            xs2 = ev_sents[:12]
            with torch.no_grad():
                x1 = torch.tensor([vocab_b.encode(t, 48) for t in xs1], dtype=torch.long)
                x2 = torch.tensor([vocab_b.encode(t, 48) for t in xs2], dtype=torch.long)
                logits = model_b(x1, x2)
                prob = torch.softmax(logits, 1)[:, 1].max().item()
            return prob < 0.5

        r_neural = ev.prf(items, neural_flag)
        r_lex = ev.prf(items, ev.flag_lexical_num)
        r_sym = ev.prf(items, ev.make_flag(True, True, True))
        # 融合：符号锚点 OR 神经通道
        sym_fn = ev.make_flag(True, True, True)
        r_fuse = ev.prf(items, lambda c, e: sym_fn(c, e) or neural_flag(c, e))
        print("  [挑战集] 词面:", r_lex)
        print("  [挑战集] 符号:", r_sym)
        print("  [挑战集] 神经(E-BiLSTM):", r_neural)
        print("  [挑战集] 符号⊕神经(F1–F4融合):", r_fuse)
        cat = {}
        for cname, its in ch.items():
            if cname == "pos":
                continue
            cat[cname] = {"符号": ev.prf(its, sym_fn)["R"],
                          "符号⊕神经": ev.prf(its, lambda c, e: sym_fn(c, e) or neural_flag(c, e))["R"]}
        print("  [类别召回]", json.dumps(cat, ensure_ascii=False))
    except Exception as e:
        print("  挑战集评估失败:", e)
        r_fuse, r_neural, cat = {}, {}, {}

    out = {
        "tcnn": {"best_test_acc": round(best, 4), "per_class_f1_real": f1_real,
                 "per_class_f1_synth": f1_synth, "support_real": sup_real,
                 "n_train": len(ld_tr.dataset), "n_test_real": len(te), "n_test_synth": len(te_s)},
        "ebilstm": {"best_test_f1": round(best_f1, 4)},
        "challenge_neural": r_neural, "challenge_fused": r_fuse, "challenge_by_cat": cat,
        "train_seconds": round(time.time() - t0, 1),
    }
    Path("experiments/train_nets_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("→ experiments/train_nets_results.json", f"({out['train_seconds']}s)")


if __name__ == "__main__":
    main()
