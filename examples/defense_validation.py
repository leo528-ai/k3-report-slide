"""
防御验证：把不同防御姿势逐一套到"长度旁路"信道上，看单判定正确率
（0.5 = 信道死透 / 1.0 = 信道打通）。纯合成仿真，无真实模型、不联网。

复用与 mock_sidechannel_demo 相同的带噪比较器：
  真→长 ~ N(4800,180)，真→短 ~ N(1200,90)，成对相减得特征差 D。

这里刻意演示几个"反直觉但真实"的结论：
  - 随机填充（零均值噪声）挡不住攻击——多加几次请求投票就把噪声平均掉了。
  - 分桶要"做对方向"：边界卡在两簇之间等于没防；桶必须粗到把两簇吞进同一个
    桶（Δ→0），但那时字段本身也基本废了。
  - 真正干净的做法（不 rehydrate 外来 opaque state）是把 oracle 从源头拿掉，
    没法用"长度变换"模拟——它直接让攻击者无处读比特。见文末与 DEFENSE.md。
"""
import random

SHORT_MU, SHORT_SD = 1200, 90
LONG_MU,  LONG_SD  = 4800, 180
PAD_SD = 4000          # 随机填充的噪声幅度（零均值，加在两条分支上）

def state_len(rng, do_long, defense):
    raw = rng.gauss(LONG_MU, LONG_SD) if do_long else rng.gauss(SHORT_MU, SHORT_SD)
    if defense == "none":
        return raw
    if defense == "normalize":          # 定长填充：无论长短都填到固定长度 → Δ→0
        return LONG_MU + rng.gauss(0, 12)
    if defense == "rand_pad":           # 随机填充：加零均值噪声，均值差 Δ 原封不动
        return raw + rng.gauss(0, PAD_SD)
    if defense == "bucket_bad":         # 分桶但边界卡在两簇之间：短→0、长→4000，仍可分
        return round(raw / 4000) * 4000
    if defense == "bucket_good":        # 粗到把两簇吞进同一个桶：Δ→0（但字段也废了）
        return round(raw / 20000) * 20000
    raise ValueError(defense)

def run_pair(rng, defense):
    a = state_len(rng, True,  defense)  # A: 真→长
    b = state_len(rng, False, defense)  # B: 真→短
    return a - b                        # 特征差 D；无防御时应 >0

def sign_vote(rng, d):
    if d > 0: return 1
    if d < 0: return -1
    return 1 if rng.random() < 0.5 else -1     # 打平 = 攻击者无信息，掷硬币

def voted_pred(rng, defense, repeats):
    v = sum(sign_vote(rng, run_pair(rng, defense)) for _ in range(repeats))
    if v == 0:
        return rng.random() < 0.5
    return v > 0

def acc(defense, repeats, n=3000, seed=2):
    rng = random.Random(seed)
    return sum(1 for _ in range(n) if voted_pred(rng, defense, repeats)) / n

def verdict(a):
    return "信道打通" if a > 0.9 else ("信道死亡" if a < 0.6 else "半通")

ROWS = [
    ("无防御(baseline)",       "none"),
    ("定长填充/长度归一化",     "normalize"),
    ("随机填充(零均值噪声)",    "rand_pad"),
    ("分桶·边界没选好",        "bucket_bad"),
    ("分桶·粗到吞掉两簇",      "bucket_good"),
]

print("="*70)
print("防御验证：正确率越接近 0.5 越好（信道死）。对比单次判定 vs 30 次投票")
print("="*70)
print(f"{'防御姿势':22s}  {'正确率@1':>9s}  {'正确率@30':>9s}   结论")
print("-"*70)
for name, d in ROWS:
    a1, a30 = acc(d, 1), acc(d, 30)
    print(f"{name:22s}  {a1:9.3f}  {a30:9.3f}   → @30:{verdict(a30)}")

print()
print("读法：")
print("  · 定长填充/粗分桶：Δ→0，@1 与 @30 都停在 ~0.5，信道死透。")
print("  · 随机填充：@1 被噪声压低，但 @30 又爬回 ~1.0——零均值噪声被投票平均掉，")
print("    多发几次请求就穿透了，噪声不是防御。")
print("  · 分桶边界没选好：短/长落进不同桶，Δ 反而更干净，等于没防。")
print("  · 最干净的做法（不 rehydrate 外来 opaque state）不在此表：它直接撤掉 oracle，")
print("    攻击者根本没有可测的长度可读。见 DEFENSE.md。")
