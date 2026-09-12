import urllib.request, ssl, hashlib, re, html, sys, json, os
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
urls=json.load(open(sys.argv[1]))
out=[]
for u in urls:
    n=hashlib.md5(u.encode()).hexdigest()[:8]
    fn=f'raw-{n}.html'
    rec={'url':u,'file':fn}
    try:
        req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml','Accept-Language':'en-US,en;q=0.9'})
        r=urllib.request.urlopen(req,timeout=40,context=ctx)
        b=r.read(); open(fn,'wb').write(b)
        rec['status']=r.status; rec['bytes']=len(b)
        t=re.search(r'<title[^>]*>(.*?)</title>',b.decode('utf-8','ignore'),re.S|re.I)
        rec['title']=html.unescape(t.group(1)).strip()[:120] if t else ''
    except Exception as e:
        rec['status']='ERR'; rec['error']=str(e)[:200]
    out.append(rec); print(rec.get('status'),rec['url'],'|',rec.get('title',''),'|',rec.get('file'),rec.get('bytes',''),rec.get('error',''))
json.dump(out,open('fetchlog.json','w'),indent=1)
