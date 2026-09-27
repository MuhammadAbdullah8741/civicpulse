"""Local k3d experiments. Python standard library only; writes genuine observations."""
import argparse
import csv
import datetime as dt
import html
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
TOOL_DIR = Path.home() / 'Tools' / 'civicpulse'
os.environ['PATH'] = str(TOOL_DIR) + os.pathsep + os.environ['PATH']
K = ['kubectl', '--context', 'k3d-civicpulse', '--request-timeout=20s']
KN = K + ['-n', 'civicpulse']
IMAGE = 'grafana/k6:0.57.0'

def run(args, **kw):
    return subprocess.run(args, check=True, text=True, **kw)

def capture(args):
    return run(args, capture_output=True).stdout

def kube(*args):
    return json.loads(capture(KN + list(args) + ['-o', 'json']))

def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

def install():
    vendor = ROOT / 'k8s/vpa/vendor'
    run(K + ['apply', '--server-side', '-f', str(vendor/'vpa-v1-crd-gen.yaml')])
    for crd in ['verticalpodautoscalers.autoscaling.k8s.io', 'verticalpodautoscalercheckpoints.autoscaling.k8s.io']:
        run(K + ['wait', '--for=condition=Established', 'crd/'+crd, '--timeout=120s'])
    run(K + ['apply', '-f', str(vendor/'vpa-rbac.yaml')])
    run(K + ['apply', '-f', str(vendor/'recommender-deployment.yaml')])
    run(K + ['-n','kube-system','rollout','status','deployment/vpa-recommender','--timeout=300s'])
    run(K + ['apply','-f','k8s/vpa/backend-vpa.yaml'])
    run(['docker','pull',IMAGE])
    print('Recommender installed. VPA is Off; it will not change pod resources.')

def snapshot():
    hpa=kube('get','hpa','backend')
    dep=kube('get','deployment','backend')
    cpu=None
    for m in hpa.get('status',{}).get('currentMetrics',[]):
        if m.get('resource',{}).get('name')=='cpu':
            cpu=m['resource'].get('current',{}).get('averageUtilization')
    return {'replicas':dep['spec'].get('replicas',0),
            'ready':dep.get('status',{}).get('readyReplicas',0),
            'desired':hpa.get('status',{}).get('desiredReplicas',0), 'cpu_percent':cpu}

def chart(rows, out):
    width,height=960,470
    max_t=max(r['seconds'] for r in rows) or 1
    max_r=max(10,max(r['replicas'] for r in rows))
    max_load=max(1,max(r['offered_rps'] for r in rows))
    def points(key,maximum):
        return ' '.join(f"{65+r['seconds']/max_t*810:.1f},{390-r[key]/maximum*300:.1f}" for r in rows)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="470" viewBox="0 0 960 470">',
           '<rect width="960" height="470" fill="white"/>',
           '<g font-family="Arial" font-size="14" fill="#172033">',
           '<text x="65" y="30" font-size="22">Backend replicas and offered load</text>',
           '<text x="65" y="55">Blue: replicas; green: ready replicas; orange: offered requests/second (right axis)</text>']
    for i in range(6):
        y=390-i*60
        parts += [f'<path d="M65 {y}H875" stroke="#ddd"/>',f'<text x="25" y="{y+5}">{max_r*i/5:g}</text>',f'<text x="887" y="{y+5}">{max_load*i/5:g}</text>']
    for key,scale,col in [('offered_rps',max_load,'#d97706'),('replicas',max_r,'#2563eb'),('ready',max_r,'#15803d')]:
        parts.append(f'<polyline points="{points(key,scale)}" fill="none" stroke="{col}" stroke-width="2"/>')
    for i in range(6):
        parts.append(f'<text x="{65+i*162}" y="415">{max_t*i/5:.0f}</text>')
    parts += ['<text x="380" y="447">Elapsed seconds from load-generator launch</text></g></svg>']
    (out/'replicas-load.svg').write_text('\n'.join(parts),encoding='utf-8')

def experiment(args):
    out=ROOT/'docs/evidence/scaling'/args.name
    if out.exists():
        raise RuntimeError(f'{out} already exists. Choose a new --name to preserve evidence.')
    initial=snapshot()
    if initial['replicas']!=2 or initial['ready']!=2:
        raise RuntimeError('Wait for backend to return to 2 ready replicas before comparison. Do not reset HPA to fake a baseline.')
    kube('get','vpa','backend-vpa')
    out.mkdir(parents=True)
    before=kube('get','deployment','backend')
    write(out/'deployment-before.json',before)
    write(out/'hpa-before.json',kube('get','hpa','backend'))
    write(out/'vpa-before.json',kube('get','vpa','backend-vpa'))
    write(out/'run.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'git_commit':capture(['git','rev-parse','HEAD']).strip(),
         'mode':args.mode,'rate':args.rate,'load_path':'/api/complaints?page=1&page_size=100','k6_image':IMAGE,'initial':initial})
    container='civicpulse-load-'+str(int(time.time()))
    rollout_process=None
    rollout_log=None
    new_image=None
    if args.mode=='rollout':
        old_image=next(c['image'] for c in before['spec']['template']['spec']['containers'] if c['name']=='backend')
        new_image=old_image+'-rollout'
        run(['docker','tag',old_image,new_image])
        run(['k3d','image','import',new_image,'-c','civicpulse'])
        write(out/'rollout-images.json',{'old':old_image,'new':new_image,'note':'Same application bytes under a new tag; exercises an image-triggered rolling update.'})
    watchfile=(out/'hpa-watch.txt').open('w',encoding='utf-8')
    watch=subprocess.Popen(['kubectl','--context','k3d-civicpulse','-n','civicpulse','get','hpa','backend','-w'],stdout=watchfile,stderr=subprocess.STDOUT,text=True)
    log=(out/'k6.log').open('w',encoding='utf-8')
    docker=['docker','run','--name',container,'--network','k3d-civicpulse',
      '--mount',f'type=bind,source={ROOT / "loadtests"},target=/tests,readonly',
      '--mount',f'type=bind,source={out},target=/results',
      '-e',f'MODE={args.mode}','-e',f'RATE={args.rate}',IMAGE,'run','--summary-export=/results/k6-summary.json','/tests/scaling.js']
    rows=[]
    start=time.monotonic()
    proc=subprocess.Popen(docker,stdout=log,stderr=subprocess.STDOUT,text=True)
    duration=210 if args.mode=='rollout' else 540
    try:
        with (out/'samples.csv').open('w',newline='',encoding='utf-8') as csvfile:
            writer=csv.DictWriter(csvfile,fieldnames=['seconds','offered_rps','replicas','ready','desired','cpu_percent'])
            writer.writeheader()
            while time.monotonic()-start<=duration:
                t=time.monotonic()-start
                # k6 container startup adds small timing uncertainty; preserve logs for interpretation.
                offered=(30 if t<180 else 0) if args.mode=='rollout' else (5 if t<30 else args.rate if t<210 else 0)
                row={'seconds':round(t,1),'offered_rps':offered,**snapshot()}
                rows.append(row);writer.writerow(row);csvfile.flush()
                print(row,flush=True)
                if args.mode=='rollout' and t>=30 and rollout_process is None:
                    run(KN+['set','image','deployment/backend',f'backend={new_image}'])
                    rollout_log=(out/'rollout-status.txt').open('w',encoding='utf-8')
                    rollout_process=subprocess.Popen(KN+['rollout','status','deployment/backend','--timeout=150s'],stdout=rollout_log,stderr=subprocess.STDOUT,text=True)
                if proc.poll() is not None and proc.returncode!=0 and t<180:
                    raise RuntimeError('Load generator stopped early. Inspect k6.log.')
                time.sleep(5)
        exit_code=proc.wait(timeout=30)
        rollout_code=rollout_process.wait(timeout=30) if rollout_process else None
    finally:
        if proc.poll() is None: run(['docker','stop',container],stdout=subprocess.DEVNULL)
        subprocess.run(['docker','rm',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        watch.terminate();watch.wait(timeout=10);watchfile.close();log.close()
        if rollout_log:rollout_log.close()
        if rows:chart(rows,out)
    write(out/'vpa-after.json',kube('get','vpa','backend-vpa'))
    (out/'vpa-describe.txt').write_text(capture(KN+['describe','vpa','backend-vpa']),encoding='utf-8')
    write(out/'deployment-after.json',kube('get','deployment','backend'))
    summary=json.loads((out/'k6-summary.json').read_text(encoding='utf-8'))
    metrics=summary.get('metrics',{})
    def value(name,key,default=0):return metrics.get(name,{}).get(key,default)
    peak=max(r['replicas'] for r in rows)
    first=next((r['seconds'] for r in rows if r['seconds']>=30 and r['replicas']>initial['replicas']),None)
    ready_first=next((r['seconds'] for r in rows if r['seconds']>=30 and r['ready']>initial['ready']),None)
    result={'load_exit_code':exit_code,'requests':value('http_reqs','count'),'failed_request_rate':value('http_req_failed','value'),
      'dropped_iterations':value('dropped_iterations','count'),'p95_ms':value('http_req_duration','p(95)'),
      'peak_replicas':peak,'scale_out_observed':peak>initial['replicas'],'first_scale_out_seconds':first,
      'first_extra_ready_seconds':ready_first,'rollout_exit_code':rollout_code,
      'timing_note':'Schedule relative to docker launch; container startup introduces a small offset. Sampling interval is ~5s plus API latency.'}
    write(out/'result.json',result)
    print(json.dumps(result,indent=2));print('Evidence:',out)
    if exit_code or not result['requests'] or (args.mode=='rollout' and rollout_code!=0):
        raise RuntimeError('Experiment did not meet success criteria; retain evidence and investigate.')
    if args.mode=='scaling' and args.require_scale_out and not result['scale_out_observed']:
        raise RuntimeError('No scale-out observed. Keep this run; repeat with a new name and higher --rate, using the same rate for the eventual comparison.')

def cpu(q):
    q=str(q)
    return float(q[:-1])/1000 if q.endswith('m') else float(q)

def memory(q):
    q=str(q)
    for suffix,mult in [('Ki',1024),('Mi',1024**2),('Gi',1024**3),('k',1000),('M',1000**2),('G',1000**3)]:
        if q.endswith(suffix):return float(q[:-len(suffix)])*mult
    return float(q)

def apply_vpa(args):
    source=ROOT/'docs/evidence/scaling'/args.name/'vpa-after.json'
    vpa=json.loads(source.read_text(encoding='utf-8'))
    recs=vpa.get('status',{}).get('recommendation',{}).get('containerRecommendations',[])
    rec=next((r for r in recs if r['containerName']=='backend'),None)
    if not rec:raise RuntimeError('No VPA recommendation yet. Collect a longer observation window first.')
    target={k:str(rec['target'][k]) for k in ['cpu','memory']}
    current=kube('get','deployment','backend')
    c=next(c for c in current['spec']['template']['spec']['containers'] if c['name']=='backend')
    limits=c['resources']['limits']
    if cpu(target['cpu'])>cpu(limits['cpu']) or memory(target['memory'])>memory(limits['memory']):
        raise RuntimeError(f'VPA target {target} exceeds limits {limits}. Review capacity/limits before applying; no changes made.')
    patch={'apiVersion':'apps/v1','kind':'Deployment','metadata':{'name':'backend','namespace':'civicpulse'},'spec':{'template':{'spec':{'containers':[{'name':'backend','resources':{'requests':target}}]}}}}
    print('Recorded recommendation:',json.dumps(rec,indent=2));print('Changing requests from',c['resources']['requests'],'to',target)
    path=ROOT/'k8s/base/backend-vpa-requests.yaml';write(path,patch)
    kust=ROOT/'k8s/base/kustomization.yaml';text=kust.read_text(encoding='utf-8')
    if 'backend-vpa-requests.yaml' not in text:
        if '\npatches:' in text:raise RuntimeError('Existing patches section requires manual review; live resources unchanged.')
        kust.write_text(text.rstrip()+'\npatches:\n- path: backend-vpa-requests.yaml\n',encoding='utf-8')
    run(['kubectl','kustomize','k8s/overlays/dev'],stdout=subprocess.DEVNULL)
    run(KN+['patch','deployment','backend','--type=strategic','--patch-file',str(path)])
    run(KN+['rollout','status','deployment/backend','--timeout=180s'])
    write(source.parent/'requests-change.json',{'before':c['resources']['requests'],'after':target,'recommendation':rec})
    print('Requests updated in cluster and Kustomize. Wait for 2 ready replicas, then rerun the same offered load.')

def compare(args):
    base=ROOT/'docs/evidence/scaling'
    for n in (args.before,args.after):
        if not n or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in n):
            raise RuntimeError('Invalid run name')
    results=[json.loads((base/n/'result.json').read_text()) for n in (args.before,args.after)]
    runs=[json.loads((base/n/'run.json').read_text()) for n in (args.before,args.after)]
    if any(r['mode']!='scaling' for r in runs) or runs[0]['rate']!=runs[1]['rate']:
        raise RuntimeError('Comparison requires two scaling runs with identical offered rates.')
    lines=['# Measured scaling comparison','',f'Runs: {args.before} and {args.after}. Offered peak rate: {runs[0]["rate"]} requests/second.','',
           '| Metric | Before | After |','|---|---:|---:|']
    for key in ['requests','failed_request_rate','dropped_iterations','p95_ms','peak_replicas','first_scale_out_seconds','first_extra_ready_seconds']:
        lines.append(f'| {key} | {results[0][key]} | {results[1][key]} |')
    lines += ['','## Resource requests','']
    for n in (args.before,args.after):
        d=json.loads((base/n/'deployment-before.json').read_text())
        c=next(x for x in d['spec']['template']['spec']['containers'] if x['name']=='backend')
        lines.append(f'- {n}: `{json.dumps(c["resources"]["requests"])}`')
    r=results[0]; first=r['first_scale_out_seconds']; ready=r['first_extra_ready_seconds']
    lines += ['','## Observed lag','',
        'The higher load was scheduled to begin 30 seconds after the load generator launched.',
        f'The first increase in desired deployment replicas was observed at {first} seconds, and extra ready capacity at {ready} seconds; a null value means it was not observed.',
        'Measurements have roughly five-second sampling resolution plus API and container startup latency.',
        'Metrics collection, HPA reconciliation and pod startup therefore separate arriving load from usable capacity, so autoscaling does not replace capacity planning.',
        'Compare failed requests and dropped iterations as well as latency before interpreting the peak replica counts.','',
        '## Why VPA is Off','',
        'HPA uses CPU usage divided by CPU requests. Automatic VPA request changes would alter that denominator while HPA adjusts replicas. Off mode records recommendations without evictions or automatic resource changes; this experiment applies one recorded target manually and repeats the same load.','',
        'This is a short local experiment on one laptop. VPA recommendations from a short observation window are provisional, not production sizing.']
    (base/'COMPARISON.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Wrote',base/'COMPARISON.md')


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    s.add_parser('install-vpa')
    e=s.add_parser('run');e.add_argument('--name',required=True);e.add_argument('--mode',choices=['scaling','rollout'],default='scaling');e.add_argument('--rate',type=int,default=200);e.add_argument('--require-scale-out',action='store_true')
    a=s.add_parser('apply-vpa');a.add_argument('--name',required=True)
    c=s.add_parser('compare');c.add_argument('--before',default='baseline');c.add_argument('--after',default='tuned')
    args=p.parse_args()
    if hasattr(args,'name') and (not args.name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.name)):
        p.error('--name must contain letters, numbers, hyphens or underscores only')
    if hasattr(args,'rate') and not 1<=args.rate<=1000:p.error('--rate must be between 1 and 1000')
    if args.command=='install-vpa':install()
    elif args.command=='run':experiment(args)
    elif args.command=='apply-vpa':apply_vpa(args)
    else:compare(args)

if __name__=='__main__':
    try:main()
    except (RuntimeError,subprocess.SubprocessError,OSError,ValueError) as exc:
        print('ERROR:',exc,file=sys.stderr);sys.exit(1)


