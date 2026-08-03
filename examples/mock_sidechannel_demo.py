"""
纯合成仿真：演示"成对反转编码 + 二分搜索"如何从长度差里读出秘密。
无任何真实模型 / provider / 加密状态——mock oracle 是一个带噪声的比较器。
确定性（固定随机种子），结果可复现。
"""
import random, math

# --- mock oracle：给定"真实答案 truth"，模拟一次请求返回的 opaque_state 长度 ---
# SHORT 分支 ~ N(1200, 90)，LONG 分支 ~ N(4800, 180)。噪声模拟排队/措辞抖动。
SHORT_MU, SHORT_SD = 1200, 90
LONG_MU,  LONG_SD  = 4800, 180

def oracle_state_len(rng, do_long):
    if do_long:
        return rng.gauss(LONG_MU, LONG_SD)
    return rng.gauss(SHORT_MU, SHORT_SD)

# 成对反转：请求A(真→长)、请求B(真→短)。D=lenA-lenB。P真→D>0，P假→D<0。
def run_pair(rng, truth, state_present=True):
    if state_present:
        a = oracle_state_len(rng, do_long=truth)       # A: true_long
        b = oracle_state_len(rng, do_long=(not truth))  # B: true_short
    else:
        # 控制组：状态被移除，模型不知道 P，长短随机 → D 是纯噪声
        a = oracle_state_len(rng, do_long=rng.random() < 0.5)
        b = oracle_state_len(rng, do_long=rng.random() < 0.5)
    return a - b  # 特征差 D

def vote_predicate(rng, truth, repeats, state_present=True):
    votes = 0
    reqs = 0
    for _ in range(repeats):
        d = run_pair(rng, truth, state_present)
        reqs += 2
        votes += 1 if d > 0 else -1
    return (votes > 0), reqs  # 多数投票判 P 真/假

# --- 二分字符集还原一个位置 ---
def recover_char(rng, secret_char, alphabet, repeats, state_present=True):
    cands = list(alphabet)
    reqs = 0
    while len(cands) > 1:
        mid = (len(cands) + 1) // 2
        left = cands[:mid]
        truth = secret_char in left            # 只有"模型"(这里是真值)知道答案
        belongs_left, r = vote_predicate(rng, truth, repeats, state_present)
        reqs += r
        cands = left if belongs_left else cands[mid:]
    return cands[0], reqs

def recover_string(secret, alphabet, repeats, seed, state_present=True):
    rng = random.Random(seed)
    out, total = [], 0
    trace = []
    for ch in secret:
        rec, r = recover_char(rng, ch, alphabet, repeats, state_present)
        out.append(rec); total += r
        trace.append((ch, rec, r))
    rec_str = "".join(out)
    return rec_str, total, trace

def sha8(s):
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()[:12]

HEX = "0123456789abcdef"
LOW = "abcdefghijklmnopqrstuvwxyz"

print("="*66)
print("例1｜合成 16 位 hex canary（正例）")
print("="*66)
sec = "3f0ac1d9b8e27f64"
rec, total, tr = recover_string(sec, HEX, repeats=3, seed=42)
print(f"secret     = {sec}")
print(f"recovered  = {rec}")
print(f"exact_match= {rec == sec}   sha256[:12]={sha8(sec)}")
print(f"字符集|Σ|=16 → 每字符 ⌈log2 16⌉=4 判定；repeats=3；理论请求 = 16×4×3×2 = {16*4*3*2}")
print(f"实测总请求 = {total}")
print("前3位轨迹(真值→还原, 该位请求数):", tr[:3])

print()
print("="*66)
print("例2｜合成小写词 'meld'（正例，换字母表）")
print("="*66)
sec2 = "meld"
rec2, total2, tr2 = recover_string(sec2, LOW, repeats=3, seed=7)
print(f"secret     = {sec2}")
print(f"recovered  = {rec2}")
print(f"exact_match= {rec2 == sec2}")
print(f"字符集|Σ|=26 → 每字符 ⌈log2 26⌉={math.ceil(math.log2(26))} 判定；理论请求 = 4×5×3×2 = {4*5*3*2}")
print(f"实测总请求 = {total2}")
print("逐位轨迹:", tr2)

print()
print("="*66)
print("例3｜控制组：移除 opaque state（同 hex canary）")
print("="*66)
rec3, total3, tr3 = recover_string(sec, HEX, repeats=3, seed=42, state_present=False)
print(f"secret     = {sec}")
print(f"recovered  = {rec3}")
print(f"exact_match= {rec3 == sec}   ← 状态缺席，判定退化为掷硬币")
# 单判定区分度：有/无 state 各测 2000 次的 |D| 均值
rngp = random.Random(1); rngn = random.Random(1)
import statistics as st
dp = [abs(run_pair(rngp, True, True))  for _ in range(2000)]
dn = [abs(run_pair(rngn, True, False)) for _ in range(2000)]
# 近似 AUC：正例 D>0 概率
rngp2 = random.Random(2)
correct = sum(1 for _ in range(4000) if run_pair(rngp2, True, True) > 0)
auc_pos = correct/4000
rngn2 = random.Random(2)
correct_n = sum(1 for _ in range(4000) if run_pair(rngn2, True, False) > 0)
auc_neg = correct_n/4000
print(f"有 state: 单判定正确率≈{auc_pos:.3f}  平均|D|≈{st.mean(dp):.0f}")
print(f"无 state: 单判定正确率≈{auc_neg:.3f}  平均|D|≈{st.mean(dn):.0f}")
