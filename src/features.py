from __future__ import annotations
import numpy as np
from scipy import signal
from scipy.fftpack import dct
try:
    import pywt
except Exception:
    pywt = None
from .config import TARGET_SR

def hz_to_mel(f):
    return 2595.0 * np.log10(1.0 + np.asarray(f) / 700.0)
def mel_to_hz(m):
    return 700.0 * (10.0 ** (np.asarray(m) / 2595.0) - 1.0)
def mel_filterbank(sr=TARGET_SR, n_fft=1024, n_mels=40, fmin=20, fmax=None):
    if fmax is None:
        fmax = sr / 2
    mels = np.linspace(float(hz_to_mel(fmin)), float(hz_to_mel(fmax)), n_mels + 2)
    hz = mel_to_hz(mels)
    bins = np.floor((n_fft + 1) * hz / sr).astype(int)
    fb = np.zeros((n_mels, n_fft // 2 + 1), dtype=np.float32)
    for i in range(1, n_mels + 1):
        left, center, right = bins[i - 1], bins[i], bins[i + 1]
        center = max(center, left + 1); right = max(right, center + 1)
        for j in range(left, min(center, fb.shape[1])):
            fb[i - 1, j] = (j - left) / max(center - left, 1)
        for j in range(center, min(right, fb.shape[1])):
            fb[i - 1, j] = (right - j) / max(right - center, 1)
    return fb
MEL_FB_40 = mel_filterbank(n_mels=40)

def _spectral_arrays_lineB(x):
    nper = min(1024, max(256, len(x)))
    freqs, times, Z = signal.stft(x, fs=TARGET_SR, window="hann", nperseg=nper, noverlap=nper//2, nfft=1024, padded=True, boundary="zeros")
    mag = np.abs(Z).astype(np.float32) + 1e-10
    return freqs, mag, mag ** 2

def lineB_feature_dict(x):
    feats = {}
    x = np.asarray(x, dtype=np.float32)
    absx = np.abs(x)
    rms = float(np.sqrt(np.mean(x*x) + 1e-12)); peak = float(np.max(absx) + 1e-12)
    feats["td_rms"] = rms; feats["td_peak"] = peak; feats["td_crest"] = peak / (rms + 1e-12)
    feats["td_zcr"] = float(np.mean(np.abs(np.diff(np.signbit(x))).astype(np.float32))) if len(x) > 1 else 0.0
    feats["td_mean_abs"] = float(np.mean(absx)); feats["td_std"] = float(np.std(x))
    feats["td_skew_proxy"] = float(np.mean(((x - np.mean(x)) / (np.std(x) + 1e-8)) ** 3))
    feats["td_kurt_proxy"] = float(np.mean(((x - np.mean(x)) / (np.std(x) + 1e-8)) ** 4))
    freqs, mag, power = _spectral_arrays_lineB(x)
    ps = power + 1e-12; ps_sum = np.sum(ps, axis=0) + 1e-12
    centroid_t = np.sum(freqs[:, None] * ps, axis=0) / ps_sum
    bandwidth_t = np.sqrt(np.sum(((freqs[:, None] - centroid_t[None, :]) ** 2) * ps, axis=0) / ps_sum)
    cumsum = np.cumsum(ps, axis=0); roll_idxs = np.argmax(cumsum >= 0.85 * ps_sum[None, :], axis=0)
    rolloff_t = freqs[roll_idxs]
    flatness_t = np.exp(np.mean(np.log(ps), axis=0)) / (np.mean(ps, axis=0) + 1e-12)
    for name, arr in [("centroid", centroid_t), ("bandwidth", bandwidth_t), ("rolloff", rolloff_t), ("flatness", flatness_t)]:
        feats[f"sp_{name}_mean"] = float(np.mean(arr)); feats[f"sp_{name}_std"] = float(np.std(arr))
    total_e = float(np.sum(ps)) + 1e-12
    for lo, hi in [(0,250),(250,500),(500,1000),(1000,2000),(2000,4000),(4000,8000)]:
        mask = (freqs >= lo) & (freqs < hi)
        feats[f"band_ratio_{lo}_{hi}"] = float(np.sum(ps[mask, :]) / total_e) if np.any(mask) else 0.0
    edges = np.linspace(0, len(freqs)-1, 7).astype(int)
    for bi in range(6):
        sl = ps[edges[bi]:max(edges[bi+1], edges[bi]+1), :]
        db = 10 * np.log10(sl + 1e-12)
        contrast = np.percentile(db, 90, axis=0) - np.percentile(db, 10, axis=0)
        feats[f"sp_contrast_b{bi}_mean"] = float(np.mean(contrast)); feats[f"sp_contrast_b{bi}_std"] = float(np.std(contrast))
    mel = np.maximum(MEL_FB_40 @ power, 1e-12); logmel = np.log(mel)
    for i in range(logmel.shape[0]):
        feats[f"logmel_{i:02d}_mean"] = float(np.mean(logmel[i])); feats[f"logmel_{i:02d}_std"] = float(np.std(logmel[i]))
    mfcc = dct(logmel, type=2, axis=0, norm="ortho")[:20]
    delta = np.diff(mfcc, axis=1) if mfcc.shape[1] > 1 else np.zeros_like(mfcc)
    for i in range(mfcc.shape[0]):
        feats[f"mfcc_{i:02d}_mean"] = float(np.mean(mfcc[i])); feats[f"mfcc_{i:02d}_std"] = float(np.std(mfcc[i]))
        feats[f"dmfcc_{i:02d}_mean"] = float(np.mean(delta[i])); feats[f"dmfcc_{i:02d}_std"] = float(np.std(delta[i]))
    if pywt is not None:
        try:
            wp = pywt.WaveletPacket(data=x, wavelet="db4", mode="symmetric", maxlevel=3)
            nodes = wp.get_level(3, order="freq")
            energies = np.array([np.sum(np.square(n.data)) for n in nodes], dtype=float)
            denom = np.sum(energies) + 1e-12
            for i, e in enumerate(energies): feats[f"wp_l3_energy_ratio_{i}"] = float(e / denom)
        except Exception:
            for i in range(8): feats[f"wp_l3_energy_ratio_{i}"] = 0.0
    else:
        for i in range(8): feats[f"wp_l3_energy_ratio_{i}"] = 0.0
    return feats

def lineA_feature_dict(y, sr=TARGET_SR):
    eps = 1e-10
    y = np.asarray(y, dtype=np.float32)
    if len(y) == 0: y = np.zeros(sr, dtype=np.float32)
    rms_frames = np.sqrt(np.maximum(signal.convolve(y * y, np.ones(max(1, sr // 100)) / max(1, sr // 100), mode="same"), 0))
    zcr = np.mean(np.abs(np.diff(np.signbit(y).astype(np.int8)))) if len(y) > 1 else 0.0
    n_fft = 1024; hop = 256
    freqs, times, zxx = signal.stft(y, fs=sr, window="hann", nperseg=n_fft, noverlap=n_fft-hop, nfft=n_fft, boundary=None)
    mag = np.abs(zxx).astype(np.float64) + eps
    power = mag * mag; psum = power.sum(axis=0) + eps
    centroid = (freqs[:, None] * power).sum(axis=0) / psum
    bandwidth = np.sqrt((((freqs[:, None] - centroid[None, :]) ** 2) * power).sum(axis=0) / psum)
    cumsum = np.cumsum(power, axis=0); roll_idx = np.argmax(cumsum >= 0.85 * psum[None, :], axis=0)
    rolloff = freqs[roll_idx]
    flatness = np.exp(np.mean(np.log(power + eps), axis=0)) / (np.mean(power + eps, axis=0) + eps)
    peak_freq = freqs[np.argmax(power.mean(axis=1))]
    total_energy = power.sum() + eps
    out = {
        "rms_mean": float(np.mean(rms_frames)), "rms_std": float(np.std(rms_frames)), "rms_max": float(np.max(rms_frames)),
        "zcr": float(zcr), "spectral_centroid_mean": float(np.mean(centroid)), "spectral_centroid_std": float(np.std(centroid)),
        "spectral_bandwidth_mean": float(np.mean(bandwidth)), "spectral_bandwidth_std": float(np.std(bandwidth)),
        "spectral_rolloff_mean": float(np.mean(rolloff)), "spectral_rolloff_std": float(np.std(rolloff)),
        "spectral_flatness_mean": float(np.mean(flatness)), "spectral_flatness_std": float(np.std(flatness)),
        "peak_frequency": float(peak_freq),
    }
    for lo, hi in [(0,500),(500,1000),(1000,2000),(2000,4000),(4000,8000)]:
        mask = (freqs >= lo) & (freqs < hi)
        out[f"band_energy_ratio_{lo}_{hi}"] = float(power[mask].sum() / total_energy) if np.any(mask) else 0.0
    for i, (lo, hi) in enumerate(zip([0,250,500,1000,2000,4000], [250,500,1000,2000,4000,8000])):
        mask = (freqs >= lo) & (freqs < min(hi, sr/2+1))
        vals = 20 * np.log10(mag[mask] + eps) if np.any(mask) else np.zeros((1, mag.shape[1]))
        contrast = np.percentile(vals, 90, axis=0) - np.percentile(vals, 10, axis=0)
        out[f"spectral_contrast_b{i}_mean"] = float(np.mean(contrast)); out[f"spectral_contrast_b{i}_std"] = float(np.std(contrast))
    mel = np.maximum(MEL_FB_40 @ power, eps); logmel = np.log(mel)
    mfcc = dct(logmel, axis=0, norm="ortho")[:13]
    delta = np.diff(mfcc, axis=1, prepend=mfcc[:, :1])
    for i in range(logmel.shape[0]):
        out[f"logmel_{i:02d}_mean"] = float(np.mean(logmel[i])); out[f"logmel_{i:02d}_std"] = float(np.std(logmel[i]))
    for i in range(mfcc.shape[0]):
        out[f"mfcc_{i:02d}_mean"] = float(np.mean(mfcc[i])); out[f"mfcc_{i:02d}_std"] = float(np.std(mfcc[i]))
        out[f"delta_mfcc_{i:02d}_mean"] = float(np.mean(delta[i])); out[f"delta_mfcc_{i:02d}_std"] = float(np.std(delta[i]))
    if len(y) > 4:
        corr = signal.correlate(y, y, mode="full", method="fft")[len(y)-1:]
        lo = max(1, sr // 1000); hi = min(len(corr), sr // 50)
        out["autocorr_peak_ratio"] = float(np.max(corr[lo:hi]) / (corr[0] + eps)) if hi > lo and corr[0] > eps else 0.0
    else:
        out["autocorr_peak_ratio"] = 0.0
    return out

def vectorize_features(feats: dict, schema: list[str]) -> np.ndarray:
    return np.array([[float(feats.get(c, 0.0)) for c in schema]], dtype=np.float32)
