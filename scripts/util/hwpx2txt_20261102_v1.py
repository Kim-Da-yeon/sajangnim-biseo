import zipfile,re,sys,html
z=zipfile.ZipFile(sys.argv[1]); out=[]
for n in sorted(x for x in z.namelist() if re.match(r'Contents/section\d+\.xml',x)):
    x=z.read(n).decode('utf8',errors='ignore')
    for p in re.findall(r'<hp:p[ >].*?</hp:p>',x,re.S):
        t=''.join(re.findall(r'<hp:t[^>]*>(.*?)</hp:t>',p,re.S)); t=html.unescape(re.sub('<[^>]+>','',t)).strip()
        if t: out.append(t)
open(sys.argv[2],'w').write('[[p1]]\n'+'\n'.join(out)); print(len(out),'문단')
