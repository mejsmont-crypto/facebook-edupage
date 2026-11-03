import json, os, urllib.parse, urllib.request, urllib.error, pathlib, datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'site'/'posts.json'
TOKEN=os.environ.get('FB_PAGE_TOKEN','').strip()
PAGE=os.environ.get('FB_PAGE_ID','').strip()
VERSION=os.environ.get('FB_API_VERSION','v26.0').strip()
if not TOKEN or not PAGE:
    raise SystemExit('Brak FB_PAGE_TOKEN lub FB_PAGE_ID w GitHub Secrets/Variables')
fields='id,message,created_time,permalink_url,full_picture,attachments{media,type,subattachments{media,type}}'
params=urllib.parse.urlencode({'fields':fields,'limit':15,'access_token':TOKEN})
url=f'https://graph.facebook.com/{VERSION}/{urllib.parse.quote(PAGE,safe="")}/published_posts?{params}'
try:
    req=urllib.request.Request(url,headers={'User-Agent':'SchoolFacebookFeed/1.0'})
    with urllib.request.urlopen(req,timeout=30) as r: data=json.load(r)
except urllib.error.HTTPError as e:
    try: detail=json.load(e).get('error',{}).get('message','')
    except Exception: detail=''
    raise SystemExit(f'Meta API HTTP {e.code}: {detail[:350]}')
if 'error' in data: raise SystemExit('Meta API: '+str(data['error'].get('message','Nieznany błąd')))

def media_urls(a):
    found=[]
    def walk(obj):
        if not isinstance(obj,dict): return
        m=obj.get('media') or {}
        u=(m.get('image') or {}).get('src')
        if isinstance(u,str) and u.startswith('https://'): found.append(u)
        for s in (obj.get('subattachments') or {}).get('data',[]):walk(s)
    for item in (a or {}).get('data',[]):walk(item)
    return list(dict.fromkeys(found))[:4]
posts=[]
for p in data.get('data',[]):
    link=p.get('permalink_url','')
    if not link.startswith('https://'):continue
    pics=media_urls(p.get('attachments'))
    if not pics and p.get('full_picture','').startswith('https://'):pics=[p['full_picture']]
    posts.append({'id':p.get('id',''),'message':p.get('message',''),'created_time':p.get('created_time',''),'url':link,'images':pics})
# Publish only after successful API request; retain last successful snapshot on errors.
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'posts':posts},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Pobrano {len(posts)} wpisów')
