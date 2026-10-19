"""Verified artifact materialization and release on GitHub Actions.

The archive contains measured local outputs. CI does not claim to rerun CAD
or certify the design. Every extracted byte is checked against a Git blob ID.
"""
from pathlib import Path,PurePosixPath
import base64,hashlib,json,os,subprocess,sys,urllib.request,urllib.error,zipfile
ROOT=Path.cwd();ARCHIVE=ROOT/'releases/L2-r3-bundle.zip'

def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def git(*args,auth=False):
    env=os.environ.copy()
    if auth:
        credential=base64.b64encode(('x-access-token:'+env['GH_TOKEN']).encode()).decode()
        env.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',GIT_CONFIG_VALUE_0='AUTHORIZATION: basic '+credential)
    return subprocess.check_output(['git',*args],env=env,text=True).strip()

def materialize(write):
    if not ARCHIVE.exists():
        pieces=sorted((ROOT/'releases').glob('L2-r3-bundle.zip.[0-9][0-9][0-9]'))
        assert pieces,'Missing release bundle segments'
        with ARCHIVE.open('wb') as stream:
            for part in pieces:stream.write(part.read_bytes())
    with zipfile.ZipFile(ARCHIVE) as z:
        manifest=json.loads(z.read('MANIFEST.json'));paths=[]
        for item in manifest:
            name=item['path'];p=PurePosixPath(name)
            assert not p.is_absolute() and '..' not in p.parts and '\\' not in name
            assert name in ['README.md','REPRODUCE.md'] or p.parts[0] in ['cad','models','views','reports','handoff','specs']
            data=z.read(name);assert len(data)==item['bytes'] and blob(data)==item['git_blob_sha'],name
            dest=ROOT/name
            if write:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            else:assert dest.read_bytes()==data,('remote output differs from reviewed artifact',name)
            paths.append(name)
    # Text files are committed atomically with the model segments.
    full=json.loads((ROOT/'releases/L2-r3-files.json').read_text())
    for item in full:
        data=(ROOT/item['path']).read_bytes()
        assert len(data)==item['bytes'] and blob(data)==item['git_blob_sha'],('Publication manifest mismatch',item['path'])
    print('Verified',len(paths),'model/view files and',len(full),'total published artifacts')
    return paths

def request(path,method='GET',data=None,content_type='application/json'):
    url=path if path.startswith('https://') else 'https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+path
    body=json.dumps(data).encode() if isinstance(data,dict) else data
    headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+os.environ['GH_TOKEN'],'X-GitHub-Api-Version':'2026-03-10','Content-Type':content_type}
    with urllib.request.urlopen(urllib.request.Request(url,data=body,headers=headers,method=method),timeout=300) as r:return json.load(r)

def main():
    action=sys.argv[1]
    if action=='expand':
        paths=materialize(True)
        git('config','user.name','github-actions[bot]');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
        git('add','--',*paths)
        if not git('diff','--cached','--name-only'):print('Artifacts already materialized');return
        git('commit','-m','Materialize reviewed L2-r3 models, checks and views')
        git('push','origin','HEAD:refs/heads/l2-r3',auth=True)
        print('Artifact commit',git('rev-parse','HEAD'));return
    assert action=='release'
    materialize(False)
    sha=git('rev-parse','HEAD');tag='L2-r3'
    try:release=request('/releases/tags/'+tag)
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
        release=request('/releases','POST',dict(tag_name=tag,target_commitish=sha,name='Quietmirror L2 r3 — INCOMPLETE',body=(ROOT/'handoff/l2_r3/RELEASE_NOTES.md').read_text(),draft=False,prerelease=True,make_latest='false'))
    assert release['prerelease'] and not release['draft'],'Existing release has incompatible status; leave unchanged'
    # Never silently move an existing tag or replace an unrelated release.
    target=request('/git/ref/tags/'+tag)['object']
    if target['type']=='tag':target=request('/git/tags/'+target['sha'])['object']
    assert target['sha']==sha,('Existing tag differs from this merge',target['sha'],sha)
    parts=ROOT/'Quietmirror_L2_r3_parts_STEP_STL.zip'
    with zipfile.ZipFile(parts,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted((ROOT/'models/L2_r3/parts').glob('*')):
            if p.suffix in ['.step','.stl']:z.write(p,p.name)
    files=[ROOT/'models/L2_r3/L2_r3_H_ALL_PARTS_SINGLE_PLATE.3mf',ROOT/'models/L2_r3/FULL_ASSEMBLY_H.step',ROOT/'models/L2_r3/FULL_ASSEMBLY_H.FCStd',ROOT/'models/L2_r3/FULL_ASSEMBLY_D_PLACEHOLDER.step',ROOT/'models/L2_r3/SIDE_MODULE_F2_TRIAL.3mf',ROOT/'views/l2_r3/L2_r3_H_SIX_VIEWS_SHEET.png',ROOT/'handoff/l2_r3/FINAL_ACCOUNTING.json',parts,ARCHIVE]
    existing={a['name']:a for a in release['assets']}
    for p in files:
        data=p.read_bytes()
        if p.name in existing:
            assert existing[p.name]['size']==len(data),('Existing asset differs; no overwrite',p.name)
            continue
        result=request(release['upload_url'].split('{')[0]+'?name='+p.name,'POST',data,'application/octet-stream')
        assert result['size']==len(data);print('Uploaded',p.name,len(data))
    print('Published prerelease',release['html_url'],'commit',sha)

if __name__=='__main__':main()
