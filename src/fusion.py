from __future__ import annotations

def fuse(lineA: dict | None, lineB: dict | None, mode: str = "fusion") -> dict:
    mode = mode or "fusion"
    a_flag = bool(lineA and lineA.get("lineA_flag"))
    b_pred = lineB.get("lineB_pred") if lineB else None
    if mode == "lineA_only":
        if lineA is None:
            return {"final_decision": "FAILED", "decision_reason": "Line A 模型不可用"}
        return {
            "final_decision": "NG" if a_flag else "OK",
            "decision_reason": "仅使用 Line A anomaly score：超过阈值判定 NG，否则 OK。",
        }
    if mode == "lineB_only":
        if lineB is None:
            return {"final_decision": "FAILED", "decision_reason": "Line B 模型不可用"}
        return {
            "final_decision": b_pred,
            "decision_reason": f"仅使用 Line B 监督分类器，判定为 {b_pred}。",
        }
    if mode == "conservative":
        if b_pred == "NG":
            return {"final_decision": "NG", "decision_reason": "保守模式：Line B 判定为 NG，建议拦截。"}
        if a_flag:
            return {"final_decision": "REVIEW", "decision_reason": "保守模式：Line A anomaly score 超过阈值，建议复核。"}
        return {"final_decision": "OK", "decision_reason": "保守模式：Line B 为 OK 且 Line A 未异常。"}
    # default fusion
    if b_pred == "NG":
        if a_flag:
            return {"final_decision": "NG", "decision_reason": "Line B 判定为 NG，Line A 也显示异常，建议拦截。"}
        return {"final_decision": "NG", "decision_reason": "Line B 判定为 NG；Line A 未强异常，但默认以 Line B 为主，建议拦截。"}
    if b_pred == "OK" and a_flag:
        return {"final_decision": "REVIEW", "decision_reason": "Line B 判定为 OK，但 Line A anomaly score 超过阈值，建议人工复核或加入新批次校准。"}
    if b_pred == "OK":
        return {"final_decision": "OK", "decision_reason": "Line B 判定为 OK，Line A anomaly score 低于阈值，判定正常。"}
    return {"final_decision": "FAILED", "decision_reason": "模型输出不完整，无法融合。"}
