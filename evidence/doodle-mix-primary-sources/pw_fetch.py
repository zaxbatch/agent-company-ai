import json,sys,hashlib,asyncio,os,re,html
from playwright.async_api import async_playwright
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
urls=json.load(open(sys.argv[1]))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--no-sandbox','--disable-blink-features=AutomationControlled'])
        ctx=await b.new_context(user_agent=UA,viewport={'width':1400,'height':1000},locale='en-US')
        for u in urls:
            n=hashlib.md5(u.encode()).hexdigest()[:8]
            rec={'url':u,'file':f'pw-{n}'}
            try:
                pg=await ctx.new_page()
                r=await pg.goto(u,wait_until='domcontentloaded',timeout=45000)
                await pg.wait_for_timeout(4000)
                txt=await pg.evaluate("()=>document.body?document.body.innerText:''")
                open(f'pw-{n}.txt','w').write(txt)
                open(f'pw-{n}.html','w').write(await pg.content())
                rec['status']=r.status if r else None; rec['chars']=len(txt)
                rec['title']=(await pg.title())[:110]
                await pg.close()
            except Exception as e:
                rec['status']='ERR'; rec['error']=str(e)[:160]
            print(json.dumps(rec),flush=True)
        await b.close()
asyncio.run(main())
