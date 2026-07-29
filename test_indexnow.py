"""Negative control: prove the keyLocation fix is load-bearing, not decorative."""
import json, urllib.request, urllib.error, re
key=open('/tmp/indexnow_key.txt').read().strip()
HOST='shantj.github.io'
sm=urllib.request.urlopen(f'https://{HOST}/sproutguard/sitemap.xml',timeout=20).read().decode()
urls=re.findall(r'<loc>(.*?)</loc>',sm)
UA={'User-Agent':'Mozilla/5.0 (compatible; IndexNowClient/1.0)'}

def call(payload):
    req=urllib.request.Request('https://www.bing.com/indexnow',data=json.dumps(payload).encode(),
        headers={'Content-Type':'application/json; charset=utf-8',**UA})
    try:
        r=urllib.request.urlopen(req,timeout=30); return r.status
    except urllib.error.HTTPError as e: return e.code

cases=[
 ('correct (keyLocation present)', {'host':HOST,'key':key,'keyLocation':f'https://{HOST}/sproutguard/{key}.txt','urlList':urls}, True),
 ('FAULT: keyLocation removed (the rounds 1-12 bug)', {'host':HOST,'key':key,'urlList':urls}, False),
 ('FAULT: keyLocation points at domain root (404)', {'host':HOST,'key':key,'keyLocation':f'https://{HOST}/{key}.txt','urlList':urls}, False),
]
passed=0
for name,payload,expect_ok in cases:
    st=call(payload); got_ok = st in (200,202)
    ok = got_ok==expect_ok
    passed+=ok
    print(f"{'PASS' if ok else 'FAIL'}  {name}: http={st} accepted={got_ok} expected={expect_ok}")
print(f"\n{passed}/{len(cases)} checks passed")
raise SystemExit(0 if passed==len(cases) else 1)
