#!/usr/bin/env python3
"""Strict data-only catalog. Production runs a reviewed copy from the ops repository."""
import argparse, hashlib, json, pathlib, re
import yaml
APPLICATION_NAMESPACES={'acceptance','multiportale-dev','multiportale-prod','bieszczady','bofh','intergol','oficyna','pbem','slezak','wspolnota'}
class Loader(yaml.SafeLoader): pass
def mapping(loader,node,deep=False):
    result={}
    for k,v in node.value:
        key=loader.construct_object(k,deep=deep)
        if key in result: raise ValueError('Duplicate YAML key')
        result[key]=loader.construct_object(v,deep=deep)
    return result
Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,mapping)
def validate(data):
    if not isinstance(data,dict) or set(data)!={'version','applications'} or type(data['version']) is not int or data['version']!=1: raise ValueError('Expected catalog version 1')
    apps=data['applications']
    if not isinstance(apps,list) or not 1<=len(apps)<=500:raise ValueError('Expected 1..500 applications')
    hosts=set()
    for a in apps:
        required={'domain','namespace','service','port'};allowed=required|{'health_path'}
        if not isinstance(a,dict) or not required.issubset(a) or not set(a).issubset(allowed):raise ValueError('Unexpected application fields')
        h=a['domain']
        if not isinstance(h,str) or not (h=='test.multi.bofh.pm' or re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.apps\.multi\.bofh\.pm',h)):raise ValueError('Reserved or unsupported domain')
        if h in hosts:raise ValueError('Duplicate domain')
        hosts.add(h)
        if a['namespace'] not in APPLICATION_NAMESPACES:raise ValueError('Namespace outside application scope')
        if not isinstance(a['service'],str) or not re.fullmatch(r'[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?',a['service']):raise ValueError('Invalid Service name')
        if type(a['port']) is not int or not 1<=a['port']<=65535:raise ValueError('Expected Service port 1..65535')
        health_path=a.get('health_path','/')
        if not isinstance(health_path,str) or len(health_path)>256 or not re.fullmatch(r'/[A-Za-z0-9._~/%:+-]*',health_path):raise ValueError('Invalid health path')
        if a['namespace']=='acceptance' and (a['service'] not in ['echo','web'] or a['port']!=80):raise ValueError('Acceptance only permits existing test services')
    return apps
def render(data):
    apps=validate(data); groups={};routes=[]
    for a in apps:
        routes.append({'domain':a['domain'],'backend':'app_'+hashlib.sha256(a['domain'].encode()).hexdigest()[:16],'health_path':a.get('health_path','/')})
        groups.setdefault(a['namespace'],[]).append({'host':a['domain'],'http':{'paths':[{'path':'/','pathType':'Prefix','backend':{'service':{'name':a['service'],'port':{'number':a['port']}}}}]}})
    manifests=[]
    for ns,rules in sorted(groups.items()):
        manifests.append({'apiVersion':'networking.k8s.io/v1','kind':'Ingress','metadata':{'name':'test-apps' if ns=='acceptance' else 'multiportale-routes','namespace':ns,'labels':{'app.kubernetes.io/managed-by':'multiportale-routing'}},'spec':{'ingressClassName':'traefik','rules':rules}})
    return {'application_routes':routes},manifests
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('catalog');p.add_argument('--output');args=p.parse_args()
    raw=pathlib.Path(args.catalog).read_bytes()
    if len(raw)>262144:raise ValueError('Catalog too large')
    data=yaml.load(raw,Loader=Loader);routes,manifests=render(data)
    if args.output:
        out=pathlib.Path(args.output);out.mkdir(parents=True,exist_ok=True)
        (out/'routes.yml').write_text(yaml.safe_dump(routes,sort_keys=False))
        (out/'ingresses.json').write_text(json.dumps({'apiVersion':'v1','kind':'List','items':manifests},indent=2)+'\n')
    print('Validated',len(routes['application_routes']),'routes')
