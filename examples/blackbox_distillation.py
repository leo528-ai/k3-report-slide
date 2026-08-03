"""
黑盒蒸馏示例：正经的做法。只用 teacher 的【可见 input→output】轨迹，
采集成 SFT 训练样本。不碰任何隐藏推理状态 / signature。

这里用一个 mock teacher 代替真实 API 调用（把 call_teacher 换成真实
provider 调用即可）。重点在于演示数据形态与采集流程，不在于攻击。
"""
import json, hashlib, time

# --- mock teacher：真实用法里换成对 provider 的一次普通请求 ---
def call_teacher(prompt: str) -> dict:
    # 真实场景：resp = client.messages.create(model=..., messages=[{"role":"user","content":prompt}])
    #          visible_text = resp.content[0].text
    # 这里用规则模拟一个可见回答（仅示意数据形态）
    canned = {
        "把 3+5 算出来":       "3 + 5 = 8。",
        "北京到上海大概多远":   "京沪高铁全程约 1318 公里，高铁约 4.5 小时。",
        "用一句话解释光合作用": "植物把光、水和二氧化碳转化成葡萄糖并释放氧气。",
    }
    return {"text": canned.get(prompt, "（示例回答）"), "model": "mock-teacher-v1"}

def collect(prompts, out_path):
    rows = []
    for p in prompts:
        r = call_teacher(p)
        sample = {
            "instruction": p,
            "input": "",
            "output": r["text"],            # 只存可见输出
            "teacher": r["model"],
            "sha256": hashlib.sha256((p + r["text"]).encode()).hexdigest()[:16],
            "ts": int(time.time()),
        }
        rows.append(sample)
    with open(out_path, "w", encoding="utf-8") as f:
        for s in rows:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    return rows

if __name__ == "__main__":
    prompts = ["把 3+5 算出来", "北京到上海大概多远", "用一句话解释光合作用"]
    rows = collect(prompts, "/tmp/distill_trajectories.jsonl")
    print("="*60)
    print("黑盒蒸馏：采集 teacher 可见轨迹（3 条）")
    print("="*60)
    for s in rows:
        print(f"[{s['teacher']}] {s['instruction']}")
        print(f"   → {s['output']}")
        print(f"   sha256={s['sha256']}")
    print()
    print(f"已写出 {len(rows)} 条 SFT 样本到 /tmp/distill_trajectories.jsonl")
    print("说明：全程只用可见 input→output，没有触碰任何 thinking.signature /")
    print("      隐藏推理。这才是可落地、合规的蒸馏数据来源。")
