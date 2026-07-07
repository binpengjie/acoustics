from __future__ import annotations
from pathlib import Path
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from .audio_io import load_for_lineA

def waveform_figure(path):
    y, sr, info = load_for_lineA(path)
    t = np.arange(len(y)) / sr
    fig, ax = plt.subplots(figsize=(8, 2.8))
    ax.plot(t, y, linewidth=0.5)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("amplitude")
    ax.set_title("Waveform")
    fig.tight_layout()
    return fig

def spectrogram_figure(path):
    y, sr, info = load_for_lineA(path)
    f, t, Z = signal.stft(y, fs=sr, nperseg=1024, noverlap=768)
    S = 20 * np.log10(np.abs(Z) + 1e-8)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    im = ax.pcolormesh(t, f, S, shading="auto", cmap="magma")
    ax.set_ylim(0, min(8000, sr / 2))
    ax.set_xlabel("time (s)")
    ax.set_ylabel("Hz")
    ax.set_title("Log spectrogram")
    fig.colorbar(im, ax=ax, label="dB")
    fig.tight_layout()
    return fig

def score_histogram_figure(df):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    if "lineA_anomaly_score" in df:
        for label, sub in df.groupby("final_decision"):
            ax.hist(sub["lineA_anomaly_score"].dropna(), bins=30, alpha=0.55, label=str(label))
        ax.set_xlabel("Line A anomaly score")
        ax.set_ylabel("count")
        ax.legend()
    fig.tight_layout()
    return fig

def save_diagnostics(path, window_scores=None, output_dir=None):
    output_dir = Path(output_dir or "outputs/diagnostics")
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(path).stem
    saved = {}

    fig = waveform_figure(path)
    waveform_path = output_dir / f"{stem}_waveform.png"
    fig.savefig(waveform_path, dpi=140)
    plt.close(fig)
    saved["waveform"] = str(waveform_path)

    fig = spectrogram_figure(path)
    spectrogram_path = output_dir / f"{stem}_spectrogram.png"
    fig.savefig(spectrogram_path, dpi=140)
    plt.close(fig)
    saved["spectrogram"] = str(spectrogram_path)

    if window_scores is not None and len(window_scores) and "window_NG_score" in window_scores:
        fig, ax = plt.subplots(figsize=(8, 2.8))
        x = window_scores.get("window_start_sec", window_scores.index)
        ax.plot(x, window_scores["window_NG_score"], marker="o", linewidth=1.0)
        ax.set_xlabel("time (s)")
        ax.set_ylabel("NG score")
        ax.set_ylim(0, 1)
        ax.set_title("Window NG score")
        fig.tight_layout()
        score_path = output_dir / f"{stem}_window_scores.png"
        fig.savefig(score_path, dpi=140)
        plt.close(fig)
        saved["window_scores"] = str(score_path)

    return saved
