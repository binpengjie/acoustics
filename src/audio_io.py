from __future__ import annotations
import math
import struct
from pathlib import Path
import numpy as np
from scipy import signal
from .config import TARGET_SR, AUDIO_EXTS

def read_wav_tolerant(path: str | Path):
    path = Path(path)
    with open(path, "rb") as f:
        blob = f.read()
    if blob[:4] != b"RIFF" or blob[8:12] != b"WAVE":
        raise ValueError("not a RIFF/WAVE file")
    offset = 12
    fmt = None
    data_bytes = None
    while offset + 8 <= len(blob):
        chunk_id = blob[offset:offset+4]
        size = int.from_bytes(blob[offset+4:offset+8], "little", signed=False)
        payload_start = offset + 8
        payload_end = min(payload_start + size, len(blob))
        payload = blob[payload_start:payload_end]
        if chunk_id == b"fmt ":
            if len(payload) < 16:
                raise ValueError("short fmt chunk")
            audio_format, channels, sr, byte_rate, block_align, bits = struct.unpack("<HHIIHH", payload[:16])
            fmt = (audio_format, channels, sr, byte_rate, block_align, bits)
        elif chunk_id == b"data":
            data_bytes = payload
        offset = payload_start + size + (size % 2)
    if fmt is None or data_bytes is None:
        raise ValueError("missing fmt or data chunk")
    audio_format, channels, sr, byte_rate, block_align, bits = fmt
    if audio_format not in (1, 3):
        raise ValueError(f"unsupported WAV format {audio_format}")
    bytes_per_sample = max(1, bits // 8)
    if not block_align or block_align < channels * bytes_per_sample:
        block_align = channels * bytes_per_sample
    frames = len(data_bytes) // block_align
    data_bytes = data_bytes[:frames * block_align]
    if audio_format == 3 and bits == 32:
        arr = np.frombuffer(data_bytes, dtype="<f4").reshape(frames, channels)
        return sr, arr.astype(np.float32), channels, bits
    if bits == 16:
        arr = np.frombuffer(data_bytes, dtype="<i2")[:frames*channels].reshape(frames, channels)
    elif bits == 24:
        raw = np.frombuffer(data_bytes, dtype=np.uint8)
        sample_bytes = raw.reshape(frames, block_align)[:, :channels*3].reshape(-1, 3).astype(np.int32)
        vals = sample_bytes[:, 0] | (sample_bytes[:, 1] << 8) | (sample_bytes[:, 2] << 16)
        vals = np.where(vals >= 2**23, vals - 2**24, vals).astype(np.int32)
        arr = vals.reshape(frames, channels)
    elif bits == 32:
        arr = np.frombuffer(data_bytes, dtype="<i4")[:frames*channels].reshape(frames, channels)
    elif bits == 8:
        arr = (np.frombuffer(data_bytes, dtype=np.uint8)[:frames*channels].astype(np.int16) - 128).reshape(frames, channels)
    else:
        raise ValueError(f"unsupported PCM bit depth {bits}")
    return sr, arr, channels, bits

def pcm_to_float_raw(data, bits: int | None = None):
    x = np.asarray(data)
    if np.issubdtype(x.dtype, np.integer):
        if bits:
            denom = float(2 ** (int(bits) - 1))
        else:
            denom = float(max(abs(np.iinfo(x.dtype).min), abs(np.iinfo(x.dtype).max)))
        x = x.astype(np.float32) / denom
    else:
        x = x.astype(np.float32)
    return np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)

def mono_average(data, bits: int | None = None) -> np.ndarray:
    x = pcm_to_float_raw(data, bits=bits)
    if x.ndim > 1:
        x = x.mean(axis=1)
    return x.astype(np.float32)

def resample_if_needed(x: np.ndarray, sr: int, target_sr: int = TARGET_SR) -> tuple[np.ndarray, int]:
    if sr != target_sr:
        g = math.gcd(int(sr), int(target_sr))
        x = signal.resample_poly(x, target_sr // g, int(sr) // g).astype(np.float32)
        sr = target_sr
    return x.astype(np.float32), int(sr)

def load_for_lineA(path: str | Path):
    original_sr, data, channels, bits = read_wav_tolerant(path)
    x = mono_average(data, bits=bits)
    x, sr = resample_if_needed(x, original_sr)
    if x.size == 0:
        x = np.zeros(1, dtype=np.float32)
    x = x - float(np.mean(x))
    max_abs = float(np.max(np.abs(x))) if x.size else 0.0
    if max_abs > 1.0:
        x = x / max_abs
    return x.astype(np.float32), sr, {"sample_rate": original_sr, "channels": channels, "bits": bits, "duration_sec": len(x)/sr}

def load_for_lineB(path: str | Path):
    original_sr, data, channels, bits = read_wav_tolerant(path)
    x = mono_average(data, bits=bits)
    x, sr = resample_if_needed(x, original_sr)
    if x.size == 0:
        x = np.zeros(1, dtype=np.float32)
    x = x - float(np.mean(x))
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak > 0:
        x = x / peak
    return x.astype(np.float32), sr, {"sample_rate": original_sr, "channels": channels, "bits": bits, "duration_sec": len(x)/sr}

def find_audio_files(path: str | Path, recursive: bool = True) -> list[Path]:
    p = Path(path)
    if p.is_file():
        return [p] if p.suffix.lower() in AUDIO_EXTS else []
    pattern = "**/*" if recursive else "*"
    return sorted([x for x in p.glob(pattern) if x.is_file() and x.suffix.lower() in AUDIO_EXTS])
