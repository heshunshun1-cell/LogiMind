"""Recompute saved FleetMind-LLM results without loading a model."""

import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
FIELDS = (
    "load_id", "truck_id", "origin_city", "destination_city", "revenue_usd",
    "fuel_used_gallons", "scheduled_delivery", "actual_delivery",
)
TIME = r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d(?:\.\d+)?)"


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rule_label(question):
    def find(prefixes):
        for prefix in prefixes:
            match = re.search(prefix + TIME, question)
            if match:
                return datetime.fromisoformat(match.group(1))
        raise ValueError("时间字段无法解析")

    plan = find(("原计划", "约定计划为"))
    actual = find(("实际完成于", "实际为"))
    return "delayed" if actual > plan else "on_time"


def score(samples, predictions):
    by_id = {row["sample_id"]: row for row in predictions}
    ids = {row["sample_id"] for row in samples}
    assert len(samples) == len(ids) == len(predictions) == len(by_id)
    assert ids == set(by_id)
    scores = Counter()
    for sample in samples:
        sid = sample["sample_id"]
        assert by_id[sid]["task"] == sample["task"]
        truth = json.loads(sample["messages"][-1]["content"])
        try:
            parsed = json.loads(by_id[sid]["prediction"])
        except (TypeError, ValueError):
            parsed = None
        if sample["task"] == "A":
            scores["A_total"] += 1
            scores["A_json"] += isinstance(parsed, dict)
            for field in FIELDS:
                expected = truth[field]
                correct = (isinstance(parsed, dict) and field in parsed
                           and type(parsed[field]) is type(expected)
                           and parsed[field] == expected)
                scores["A_fields"] += correct
                if expected is None:
                    scores["A_null_total"] += 1
                    scores["A_null"] += correct
        else:
            scores["B_total"] += 1
            predicted = (parsed.get("delay_label")
                         if isinstance(parsed, dict) and set(parsed) == {"delay_label"}
                         else None)
            scores["B_correct"] += predicted == truth["delay_label"]
    return scores


def main():
    sets = {name: rows(DATA / (name + ".jsonl"))
            for name in ("train_e1", "train_e2", "train_e3", "val", "test")}
    expected = {"train_e1": 1600, "train_e2": 4000, "train_e3": 8000,
                "val": 1000, "test": 2000}
    assert all(len(sets[k]) == v for k, v in expected.items())
    ids = {k: {r["sample_id"] for r in v} for k, v in sets.items()}
    loads = {k: {r["source_load_id"] for r in v} for k, v in sets.items()}
    assert ids["train_e1"] < ids["train_e2"] < ids["train_e3"]
    assert not (loads["train_e3"] & loads["val"]
                or loads["train_e3"] & loads["test"]
                or loads["val"] & loads["test"])
    selection = json.loads((RESULTS / "phase5/final_model_selection.json").read_text())
    test_metrics = json.loads((RESULTS / "phase5/E1_final_test_metrics.json").read_text())
    assert sha(DATA / "val.jsonl") == selection["validation_sha256"]
    assert sha(DATA / "test.jsonl") == test_metrics["test_sha256"]

    print("Phase 4: same Val, strict raw-output scoring")
    for method, counts in (("zero_shot", (1, 7, 334)),
                           ("few_shot", (500, 3963, 311)),
                           ("lora", (500, 4000, 497))):
        path = RESULTS / "phase4" / (method + "_val_predictions.jsonl")
        s = score(sets["val"], rows(path))
        assert (s["A_json"], s["A_fields"], s["B_correct"]) == counts
        assert (s["A_total"], s["B_total"]) == (500, 500)
        print(f"  {method}: JSON {s['A_json']}/500; fields {s['A_fields']}/4000; B {s['B_correct']}/500")
    assert sha(RESULTS / "phase4/lora_val_predictions.jsonl") == (
        "02e6e5bbdf487e74903d18f0ba3ba3ad0f0537708cdb9bf650f2e5394369bbe3")
    rule_correct = sum(rule_label(x["messages"][1]["content"]) ==
                       json.loads(x["messages"][-1]["content"])["delay_label"]
                       for x in sets["val"] if x["task"] == "B")
    assert rule_correct == 500
    print("  rule: B 500/500")

    print("Phase 5: saved predictions against the same Val and sealed Test")
    for experiment, b in (("E1", 497), ("E2", 497), ("E3", 437)):
        p = RESULTS / "phase5/predictions" / (experiment + "_val_predictions.jsonl")
        s = score(sets["val"], rows(p))
        assert (s["A_fields"], s["B_correct"]) == (4000, b)
        print(f"  {experiment} Val: fields {s['A_fields']}/4000; B {s['B_correct']}/500")
    test = score(sets["test"], rows(RESULTS / "phase5/predictions/E1_test_predictions.jsonl"))
    assert (test["A_fields"], test["B_correct"]) == (8000, 1000)
    print("  E1 Test: fields 8000/8000; B 1000/1000")
    challenge_path = DATA / "phase4_challenge_100.jsonl"
    assert sha(challenge_path) == "36cab650f9053c9d96137a5ca3f77ecbb87e2bf6b04080f0abb1602512ccac64"
    challenge = score(rows(challenge_path), rows(RESULTS / "phase4/phase4_lora_challenge_predictions.jsonl"))
    assert (challenge["A_total"], challenge["B_total"]) == (50, 50)
    assert (challenge["A_json"], challenge["A_fields"], challenge["A_null"], challenge["A_null_total"]) == (50, 400, 49, 49)
    assert challenge["B_correct"] == 45
    print("Challenge: A fields 400/400; null 49/49; B 45/50")
    print("Verified. These are results for this synthetic, same-source dataset.")


if __name__ == "__main__":
    main()
