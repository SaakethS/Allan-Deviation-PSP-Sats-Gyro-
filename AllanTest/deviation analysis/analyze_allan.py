"""Overlapping Allan deviation of timestamped gyro rates (rad/s).
Usage: python analyze_allan.py input.csv [output_directory]
Requires numpy and matplotlib. No detrending, interpolation or outlier removal.
"""
from pathlib import Path
import sys, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def oadev(rate, ms):
    # Adjacent m-sample averages, shifted by one sample (fully overlapping).
    centered = rate - np.mean(rate, axis=0)
    cs = np.vstack([np.zeros(3), np.cumsum(centered, axis=0)])
    result = []
    for m in ms:
        delta = (cs[2*m:] - 2*cs[m:-m] + cs[:-2*m]) / m
        result.append(np.sqrt(np.mean(delta**2, axis=0)/2))
    return np.asarray(result)

def main():
    source = Path(sys.argv[1]); out = Path(sys.argv[2]) if len(sys.argv)>2 else Path('allan_results')
    out.mkdir(parents=True, exist_ok=True)
    a = np.loadtxt(source, delimiter=',', skiprows=1)
    if a.ndim != 2 or a.shape[1] != 4 or not np.isfinite(a).all():
        raise ValueError('Expected finite timestamp and three gyro columns.')
    elapsed = (a[:,0]-a[0,0])*1e-6
    intervals = np.diff(elapsed)
    if np.any(intervals<=0): raise ValueError('Timestamps must increase; unwrap any timer rollover first.')
    dt = float(np.mean(intervals)); fs = 1/dt
    if np.max(intervals)>1.5*dt: raise ValueError('Timing gap detected; segment data before analysis.')
    # Full record retained for comparison. Omit first 10 min for primary estimates.
    use = elapsed >= 600
    rate = a[use,1:]
    ms = np.unique(np.geomspace(1, len(rate)//20, 100).astype(int))
    tau = ms*dt
    adev = oadev(rate, ms); full = oadev(a[:,1:], ms)
    np.savetxt(out/'allan_deviation.csv', np.column_stack([tau, ms, adev, full]), delimiter=',',
               header='tau_s,cluster_samples,x_rad_s,y_rad_s,z_rad_s,x_full_rad_s,y_full_rad_s,z_full_rad_s', comments='')
    summary = {'samples':len(a), 'duration_hours':float(elapsed[-1]/3600), 'sample_rate_hz':fs,
               'discarded_warmup_seconds':600, 'analyzed_samples':len(rate), 'max_tau_s':float(tau[-1]),
               'timing_interval_percentiles_ms':np.percentile(intervals*1000,[0,1,50,99,100]).tolist(),
               'mean_rate_rad_s':np.mean(rate,axis=0).tolist(), 'axes':{}}
    for k,name in enumerate('XYZ'):
        fit=(tau>=0.1)&(tau<=1.0)
        slope,intercept=np.polyfit(np.log(tau[fit]),np.log(adev[fit,k]),1)
        N=float(np.exp(np.mean(np.log(adev[fit,k])+0.5*np.log(tau[fit]))))
        i=int(np.argmin(adev[:,k]))
        summary['axes'][name]={'arw_fit_range_s':[0.1,1], 'fitted_slope':float(slope),
            'arw_rad_sqrt_s':N, 'arw_deg_sqrt_hour':N*180/np.pi*60,
            'minimum_adev_rad_s':float(adev[i,k]), 'minimum_tau_s':float(tau[i]),
            'minimum_div_0_664_deg_hour':float(adev[i,k]/np.sqrt(2*np.log(2)/np.pi)*180/np.pi*3600)}
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    fig,ax=plt.subplots(figsize=(10,6),layout='constrained')
    colors=['#2166ac','#d6604d','#27835b']
    for k,name in enumerate('XYZ'):
        ax.loglog(tau,adev[:,k]*180/np.pi,label=f'{name} axis',color=colors[k],lw=2)
        ax.loglog(tau,full[:,k]*180/np.pi,color=colors[k],lw=1,ls=':',alpha=.55)
    ax.set(xlabel='Averaging time, τ (seconds)',ylabel='Allan deviation (degrees/second)',
           title='Gyroscope overlapping Allan deviation')
    ax.grid(True,which='both',alpha=.2); ax.legend()
    fig.set_layout_engine('constrained', rect=(0, .06, 1, .94))
    fig.text(.5,.015,'Solid: first 10 minutes excluded • Dotted: complete 8.95-hour recording',ha='center',fontsize=10)
    fig.savefig(out/'allan_deviation.png',dpi=180); fig.savefig(out/'allan_deviation.pdf')
    plt.close(fig)
    # Minute means expose warm-up / long-term drift without filtering Allan inputs.
    bins=(elapsed//60).astype(int)
    bt=[]; means=[]
    for b in np.unique(bins):
        sel=bins==b; bt.append(np.mean(elapsed[sel])/3600); means.append(np.mean(a[sel,1:],axis=0))
    fig,axes=plt.subplots(3,1,figsize=(10,7),sharex=True,layout='constrained')
    for k,name in enumerate('XYZ'):
        axes[k].plot(bt,np.array(means)[:,k]*180/np.pi,color=colors[k])
        axes[k].set_ylabel(f'{name} (deg/s)'); axes[k].grid(alpha=.2)
    axes[0].set_title('Gyro rate: one-minute averages'); axes[-1].set_xlabel('Time since recording began (hours)')
    fig.savefig(out/'gyro_drift.png',dpi=180); plt.close(fig)
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
