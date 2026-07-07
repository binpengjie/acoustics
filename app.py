from __future__ import annotations
import tempfile
from pathlib import Path
import pandas as pd
import streamlit as st

from src.batch_inference import infer_path
from src.lineA_mahalanobis import LineAMahalanobis
from src.lineB_classifier import LineBClassifier
from src.fusion import fuse
from src.visualization import waveform_figure, spectrogram_figure, score_histogram_figure
from src.reporting import validation_report
from src.config import HISTORY_DIR, REPORTS_DIR
from src.utils import timestamp, friendly_error, read_json

st.set_page_config(page_title="声学 OK/NG 检测", layout="wide")
MODE_LABELS = {"fusion": "融合模式（推荐）", "lineB_only": "仅 Line B", "lineA_only": "仅 Line A", "conservative": "保守模式"}
STATUS_CN = {"OK": "正常 OK", "NG": "异常 NG", "REVIEW": "需要复核 REVIEW", "FAILED": "处理失败 FAILED"}

@st.cache_resource
def load_models():
    return LineAMahalanobis(), LineBClassifier()

def sidebar_settings():
    st.sidebar.header("运行设置")
    mode_cn = st.sidebar.selectbox("检测模式", list(MODE_LABELS.values()), index=0)
    mode = {v:k for k,v in MODE_LABELS.items()}[mode_cn]
    default_thr = LineAMahalanobis().threshold
    thr = st.sidebar.number_input("Line A 临时阈值", value=float(default_thr), step=1.0)
    st.sidebar.warning("降低阈值会提高 NG 检出率，但增加 OK 误报；提高阈值会减少误报，但可能漏检 NG。")
    return mode, thr

def result_card(decision):
    color = {"OK": "#DCFCE7", "NG": "#FEE2E2", "REVIEW": "#FEF3C7", "FAILED": "#E5E7EB"}.get(decision, "#E5E7EB")
    st.markdown(f"<div style='background:{color};padding:18px;border-radius:8px;font-size:28px;font-weight:700'>{STATUS_CN.get(decision, decision)}</div>", unsafe_allow_html=True)

def single_file_page(mode, thr):
    st.title("首页 / 单文件检测")
    up = st.file_uploader("上传一个 WAV 音频文件", type=["wav","wave","flac","mp3","m4a"])
    if up and st.button("开始检测", type="primary"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(up.name).suffix) as tmp:
            tmp.write(up.getbuffer())
            p = Path(tmp.name)
        try:
            la = LineAMahalanobis(threshold_override=thr)
            lb = None if mode == "lineA_only" else LineBClassifier()
            a = la.predict_file(p) if mode != "lineB_only" else None
            b = lb.predict_file(p) if lb else None
            dec = fuse(a, b, mode)
            result_card(dec["final_decision"])
            st.write(dec["decision_reason"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Line B", b["lineB_pred"] if b else "未启用", None if not b else f"{b['lineB_score_or_probability']:.3f}")
            c2.metric("Line A score", "未启用" if not a else f"{a['lineA_anomaly_score']:.3f}")
            c3.metric("Line A margin", "未启用" if not a else f"{a['lineA_margin']:.3f}")
            if a and a.get("lineA_top_features"):
                st.subheader("主要异常贡献特征")
                st.dataframe(pd.DataFrame(a["lineA_top_features"]), use_container_width=True)
            st.subheader("波形")
            st.pyplot(waveform_figure(p))
            st.subheader("频谱图")
            st.pyplot(spectrogram_figure(p))
        except Exception as e:
            result_card("FAILED")
            st.error(friendly_error(e))

def batch_page(mode, thr):
    st.title("批量检测")
    folder = st.text_input("本地文件夹路径（Windows 例如 C:\\audio_batch）")
    recursive = st.checkbox("递归扫描子文件夹", value=True)
    uploads = st.file_uploader("或上传多个音频文件", type=["wav","wave","flac","mp3","m4a"], accept_multiple_files=True)
    if st.button("开始批量检测", type="primary"):
        if uploads:
            tmpdir = Path(tempfile.mkdtemp())
            for u in uploads:
                (tmpdir / u.name).write_bytes(u.getbuffer())
            target = tmpdir
        else:
            target = Path(folder)
        df = infer_path(target, mode=mode, recursive=recursive, threshold_override=thr)
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        out = HISTORY_DIR / f"inference_{timestamp()}.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        st.session_state["last_batch"] = df
        st.success(f"结果已保存: {out}")
    if "last_batch" in st.session_state:
        df = st.session_state["last_batch"]
        ok = (df.final_decision == "OK").sum(); ng = (df.final_decision == "NG").sum(); rev = (df.final_decision == "REVIEW").sum(); fail = (df.final_decision == "FAILED").sum()
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("总数", len(df)); c2.metric("OK", ok); c3.metric("NG", ng); c4.metric("REVIEW", rev); c5.metric("失败", fail)
        filt = st.multiselect("筛选结果", ["OK","NG","REVIEW","FAILED"], default=["OK","NG","REVIEW","FAILED"])
        st.dataframe(df[df.final_decision.isin(filt)], use_container_width=True)
        st.download_button("导出 CSV", data=df.to_csv(index=False, encoding="utf-8-sig"), file_name="okng_results.csv")
        st.pyplot(score_histogram_figure(df))

def model_page():
    st.title("模型解释 / 可视化")
    st.markdown("""
    - **Line B**：主生产 OK/NG 监督分类器，ExtraTrees_balanced，预期 NG FNR 约 0.0075。
    - **Line A**：OK 分布异常监控器，Mahalanobis 距离，预期 NG FNR 约 0.0477。
    - 默认融合：Line B 判 NG 则 NG；Line B 判 OK 且 Line A 正常则 OK；Line B 判 OK 但 Line A 异常则 REVIEW。
    """)
    if "last_batch" in st.session_state:
        st.pyplot(score_histogram_figure(st.session_state["last_batch"]))

def settings_page(mode, thr):
    st.title("阈值与运行模式设置")
    st.write(f"当前临时模式：{MODE_LABELS[mode]}")
    st.write(f"当前临时 Line A 阈值：{thr}")
    st.warning("此页面的阈值调整仅在当前 UI 会话中生效，不会覆盖默认模型阈值。")

def validation_page(mode, thr):
    st.title("新批次校准 / 验证")
    st.write("支持带 OK/NG 子目录的文件夹，例如 batch/OK/*.wav 和 batch/NG/*.wav。")
    folder = st.text_input("带标签的新批次文件夹路径")
    if st.button("运行新批次验证", type="primary") and folder:
        df = infer_path(folder, mode=mode, recursive=True, threshold_override=thr)
        val_df, md = validation_report(df)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = timestamp()
        csv_path = REPORTS_DIR / f"fresh_batch_validation_{ts}.csv"
        md_path = REPORTS_DIR / f"fresh_batch_validation_{ts}.md"
        val_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        md_path.write_text(md, encoding="utf-8")
        st.markdown(md)
        st.dataframe(val_df, use_container_width=True)
        st.success(f"报告已保存: {csv_path}")

def help_page():
    st.title("帮助 / 使用说明")
    st.markdown(Path("docs/USER_MANUAL.md").read_text(encoding="utf-8"))

mode, thr = sidebar_settings()
page = st.sidebar.radio("页面", ["首页 / 单文件检测", "批量检测", "模型解释 / 可视化", "阈值与运行模式设置", "新批次校准 / 验证", "帮助 / 使用说明"])
if page == "首页 / 单文件检测": single_file_page(mode, thr)
elif page == "批量检测": batch_page(mode, thr)
elif page == "模型解释 / 可视化": model_page()
elif page == "阈值与运行模式设置": settings_page(mode, thr)
elif page == "新批次校准 / 验证": validation_page(mode, thr)
else: help_page()
