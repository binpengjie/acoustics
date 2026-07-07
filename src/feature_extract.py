from __future__ import annotations
from functools import lru_cache
import numpy as np, pandas as pd, pywt
from scipy import signal
from scipy.fftpack import dct
TARGET_SR=16000
BANDS=[(0,250),(250,500),(500,1000),(1000,2000),(2000,4000),(4000,8000)]
META_COLUMNS={"file_id","window_index","window_start_sample_16k","window_tag","label","label_name","path","relative_path"}
def hz_to_mel(f): return 2595.0*np.log10(1.0+np.asarray(f)/700.0)
def mel_to_hz(m): return 700.0*(10.0**(np.asarray(m)/2595.0)-1.0)
@lru_cache(maxsize=32)
def mel_filterbank(sr:int=TARGET_SR,n_fft:int=1024,n_mels:int=40,fmin:int=20,fmax:int|None=None):
    if fmax is None: fmax=sr//2
    hz=mel_to_hz(np.linspace(hz_to_mel(fmin),hz_to_mel(fmax),n_mels+2)); bins=np.floor((n_fft+1)*hz/sr).astype(int)
    fb=np.zeros((n_mels,n_fft//2+1),dtype=np.float32)
    for i in range(1,n_mels+1):
        left,center,right=bins[i-1],bins[i],bins[i+1]; center=max(center,left+1); right=max(right,center+1)
        for j in range(left,min(center,fb.shape[1])): fb[i-1,j]=(j-left)/max(center-left,1)
        for j in range(center,min(right,fb.shape[1])): fb[i-1,j]=(right-j)/max(right-center,1)
    return fb
def make_windows(x, win_sec, sr:int=TARGET_SR):
    if win_sec is None: return [(0,x)]
    n=max(1,int(round(float(win_sec)*sr)))
    if len(x)<=n:
        y=np.zeros(n,dtype=np.float32); y[:len(x)]=x; return [(0,y)]
    out=[(start,x[start:start+n]) for start in range(0,len(x)-n+1,n)]
    return out or [(0,x[:n])]
def spectral_arrays(x):
    nper=min(1024,max(256,len(x))); nover=nper//2
    freqs,t,z=signal.stft(x,fs=TARGET_SR,window="hann",nperseg=nper,noverlap=nover,nfft=1024,padded=True,boundary="zeros")
    mag=np.abs(z).astype(np.float32)+1e-10; return freqs,mag,mag**2
def feature_vector(x):
    feats={}; x=np.asarray(x,dtype=np.float32); x=x if x.size else np.zeros(1,dtype=np.float32); absx=np.abs(x)
    rms=float(np.sqrt(np.mean(x*x)+1e-12)); peak=float(np.max(absx)+1e-12)
    feats.update({"td_rms":rms,"td_peak":peak,"td_crest":peak/(rms+1e-12),"td_zcr":float(np.mean(np.abs(np.diff(np.signbit(x))).astype(np.float32))) if len(x)>1 else 0.0,"td_mean_abs":float(np.mean(absx)),"td_std":float(np.std(x)),"td_skew_proxy":float(np.mean(((x-np.mean(x))/(np.std(x)+1e-8))**3)),"td_kurt_proxy":float(np.mean(((x-np.mean(x))/(np.std(x)+1e-8))**4))})
    freqs,mag,power=spectral_arrays(x); ps=power+1e-12; ps_sum=np.sum(ps,axis=0)+1e-12
    centroid_t=np.sum(freqs[:,None]*ps,axis=0)/ps_sum; bandwidth_t=np.sqrt(np.sum(((freqs[:,None]-centroid_t[None,:])**2)*ps,axis=0)/ps_sum)
    cumsum=np.cumsum(ps,axis=0); roll_idxs=np.argmax(cumsum>=0.85*ps_sum[None,:],axis=0); rolloff_t=freqs[roll_idxs]; flatness_t=np.exp(np.mean(np.log(ps),axis=0))/(np.mean(ps,axis=0)+1e-12)
    for name,arr in [("centroid",centroid_t),("bandwidth",bandwidth_t),("rolloff",rolloff_t),("flatness",flatness_t)]: feats[f"sp_{name}_mean"]=float(np.mean(arr)); feats[f"sp_{name}_std"]=float(np.std(arr))
    total_e=float(np.sum(ps))+1e-12
    for lo,hi in BANDS:
        mask=(freqs>=lo)&(freqs<hi); feats[f"band_ratio_{lo}_{hi}"]=float(np.sum(ps[mask,:])/total_e) if np.any(mask) else 0.0
    edges=np.linspace(0,len(freqs)-1,7).astype(int)
    for bi in range(6):
        sl=ps[edges[bi]:max(edges[bi+1],edges[bi]+1),:]; db=10*np.log10(sl+1e-12); contrast=np.percentile(db,90,axis=0)-np.percentile(db,10,axis=0)
        feats[f"sp_contrast_b{bi}_mean"]=float(np.mean(contrast)); feats[f"sp_contrast_b{bi}_std"]=float(np.std(contrast))
    logmel=np.log(np.maximum(mel_filterbank()@power,1e-12))
    for i in range(logmel.shape[0]): feats[f"logmel_{i:02d}_mean"]=float(np.mean(logmel[i])); feats[f"logmel_{i:02d}_std"]=float(np.std(logmel[i]))
    mfcc=dct(logmel,type=2,axis=0,norm="ortho")[:20]; delta=np.diff(mfcc,axis=1) if mfcc.shape[1]>1 else np.zeros_like(mfcc)
    for i in range(mfcc.shape[0]):
        feats[f"mfcc_{i:02d}_mean"]=float(np.mean(mfcc[i])); feats[f"mfcc_{i:02d}_std"]=float(np.std(mfcc[i])); feats[f"dmfcc_{i:02d}_mean"]=float(np.mean(delta[i])); feats[f"dmfcc_{i:02d}_std"]=float(np.std(delta[i]))
    try:
        wp=pywt.WaveletPacket(data=x,wavelet="db4",mode="symmetric",maxlevel=3); nodes=wp.get_level(3,order="freq"); energies=np.array([np.sum(np.square(n.data)) for n in nodes],dtype=float); denom=np.sum(energies)+1e-12
        for i,e in enumerate(energies): feats[f"wp_l3_energy_ratio_{i}"]=float(e/denom)
    except Exception:
        for i in range(8): feats[f"wp_l3_energy_ratio_{i}"]=0.0
    return feats
def extract_full_features(x, feature_names=None):
    row=feature_vector(x); row={name:row.get(name,0.0) for name in feature_names} if feature_names else row; return pd.DataFrame([row])
def extract_window_features(x, window_sec=4.0, feature_names=None):
    rows=[]
    for idx,(start,w) in enumerate(make_windows(x,window_sec)):
        row=feature_vector(w); row={name:row.get(name,0.0) for name in feature_names} if feature_names else row; row["window_index"]=idx; row["window_start_sec"]=start/TARGET_SR; row["window_end_sec"]=(start+len(w))/TARGET_SR; rows.append(row)
    return pd.DataFrame(rows)
def align_feature_frame(df, feature_names):
    out=df.copy()
    for name in feature_names:
        if name not in out.columns: out[name]=0.0
    return out[feature_names].replace([np.inf,-np.inf],np.nan).astype(np.float32)
