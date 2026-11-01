"""Describe churn rates by recorded complaint, tariff and charge codes."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SEGMENTS = ['Complains', 'Tariff_Plan', 'Charge_Amount']

def analyze(frame):
    required = ['Customer_ID', 'Churn'] + SEGMENTS
    if not set(required).issubset(frame.columns):
        raise ValueError('Required columns: ' + ', '.join(required))
    d = frame[required].copy()
    if d.empty or d.Customer_ID.isna().any() or d.Customer_ID.astype(str).str.strip().eq('').any():
        raise ValueError('Nonempty data and customer IDs are required')
    if d.Customer_ID.duplicated().any():
        raise ValueError('Customer IDs must be unique')
    d[['Churn']+SEGMENTS] = d[['Churn']+SEGMENTS].apply(pd.to_numeric, errors='raise')
    if not d.Churn.isin([0,1]).all():
        raise ValueError('Churn must be 0 or 1 with no missing values')
    for col, allowed in [('Complains',[0,1]),('Tariff_Plan',[1,2]),('Charge_Amount',list(range(11)))]:
        if not d[col].dropna().isin(allowed).all():
            raise ValueError(f'Unsupported code in {col}')
    rows=[]
    for col in SEGMENTS:
        codes=d[col].map(lambda v: 'Missing' if pd.isna(v) else str(int(v)))
        for code, group in d.groupby(codes, sort=True):
            n=len(group); k=int(group.Churn.sum()); rate=k/n
            # Wilson score interval, 95%, z = 1.959963984540054.
            z=1.959963984540054; denominator=1+z*z/n
            center=(rate+z*z/(2*n))/denominator
            half=z*np.sqrt(rate*(1-rate)/n+z*z/(4*n*n))/denominator
            rows.append(dict(segment=col,code=code,customers=n,churned=k,
                             churn_rate=rate,lower_95=max(0.,center-half),upper_95=min(1.,center+half)))
    summary={'customers':len(d),'churned':int(d.Churn.sum()),'churn_rate':float(d.Churn.mean()),
             'missing_segment_values':{c:int(d[c].isna().sum()) for c in SEGMENTS}}
    return pd.DataFrame(rows),summary

def run(source,output):
    table,summary=analyze(pd.read_csv(source));output=Path(output);output.mkdir(parents=True,exist_ok=True)
    table.to_csv(output/'segment_rates.csv',index=False)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    plot=table[table.segment=='Complains']
    fig,ax=plt.subplots(figsize=(8,4.5))
    ax.bar(plot.code,plot.churn_rate*100,color='#267D9C')
    ax.errorbar(plot.code,plot.churn_rate*100,
                yerr=[(plot.churn_rate-plot.lower_95)*100,(plot.upper_95-plot.churn_rate)*100],
                fmt='none',ecolor='#222222',capsize=5)
    ax.set(xlabel='Recorded complaint code',ylabel='Churn rate (%)',title='Churn by complaint code with 95% Wilson intervals',ylim=(0,100))
    for i,row in enumerate(plot.itertuples()): ax.text(i,2,f'n={row.customers}',ha='center',color='black')
    fig.tight_layout();fig.savefig(output/'complaint_churn.svg');plt.close(fig)
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path,default=Path('results'));args=parser.parse_args()
    print(json.dumps(run(args.input,args.output),indent=2))
