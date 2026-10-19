"""Publish only an all-CAD-gates-complete main merge; never alter old releases."""
from pathlib import Path
import json,os,subprocess,urllib.request,urllib.error,urllib.parse,zipfile
ROOT=Path.cwd();TAG='L2-r4'

def request(path,method='GET',data=None,content_type='application/json'):
    url=path if path.startswith('https://') else 'https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+path
    body=json.dumps(data).encode() if isinstance(data,dict) else data
    headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+os.environ['GH_TOKEN'],'X-GitHub-Api-Version':'2022-11-28','Content-Type':content_type}
    with urllib.request.urlopen(urllib.request.Request(url,data=body,headers=headers,method=method),timeout=300) as response:return json.load(response)

def main():
    accounting=json.loads((ROOT/'handoff/l2_r4/FINAL_ACCOUNTING.json').read_text())
    assert accounting['status']=='CAD_COMPLETE / HARDWARE_PENDING'
    gates=accounting['gates'];assert set(gates)=={f'G{i}' for i in range(1,12)}
    assert all(row['status']=='COMPLETED' for row in gates.values()),'A CAD gate is not completed; release prohibited'
    assert len(json.loads((ROOT/'reports/l2_r4/solids.json').read_text()))==9
    native=json.loads((ROOT/'reports/l2_r4/native_roundtrip.json').read_text())
    assert native['all_valid'] and len(native['parts'])>=89 and native['full_step_roundtrip']['valid']
    fem=json.loads((ROOT/'reports/l2_r4/fem/G8.json').read_text());assert fem['status']=='COMPLETED' and len(fem['rows'])==18
    stress=json.loads((ROOT/'reports/l2_r4/fem/S7.json').read_text());assert stress['status']=='COMPLETED' and len(stress['rows'])==12
    sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert os.environ['GITHUB_REF']=='refs/heads/main','Only an authorized main merge may release'
    try:release=request('/releases/tags/'+TAG)
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
        release=request('/releases','POST',dict(tag_name=TAG,target_commitish=sha,
            name='Quietmirror L2 r4 — CAD COMPLETE / HARDWARE PENDING',
            body=(ROOT/'handoff/l2_r4/RELEASE_NOTES.md').read_text(),draft=False,prerelease=False,make_latest='true'))
    assert not release['prerelease'] and not release['draft']
    ref=request('/git/ref/tags/'+TAG)['object']
    if ref['type']=='tag':ref=request('/git/tags/'+ref['sha'])['object']
    assert ref['sha']==sha,'Existing r4 tag points elsewhere; do not move or replace it'
    archive=ROOT/'Quietmirror_L2_r4_parts_STEP_STL.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted((ROOT/'models/L2_r4/parts').glob('*')):
            if path.suffix in ['.step','.stl']:z.write(path,path.name)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    files=[ROOT/'models/L2_r4/L2_r4_H_ALL_PARTS_SINGLE_PLATE.3mf',ROOT/'models/L2_r4/FULL_ASSEMBLY_H.step',
           ROOT/'models/L2_r4/FULL_ASSEMBLY_H.FCStd',ROOT/'models/L2_r4/D_MAX_BOARD_ENVELOPE.step',
           ROOT/'models/L2_r4/SIDE_MODULE_F2_TRIAL.3mf',ROOT/'views/l2_r4/L2_r4_H_SIX_VIEWS_SHEET.png',
           ROOT/'handoff/l2_r4/FINAL_ACCOUNTING.json',ROOT/'handoff/l2_r4/GATES.md',archive]
    existing={item['name']:item for item in release['assets']}
    for path in files:
        data=path.read_bytes()
        if path.name in existing:
            assert existing[path.name]['size']==len(data),'Existing asset size differs; no overwrite'
            continue
        upload=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(path.name)
        asset=request(upload,'POST',data,'application/octet-stream');assert asset['size']==len(data)
        print('RELEASE_ASSET',asset['browser_download_url'],flush=True)
    print('RELEASE',release['html_url'],'commit',sha,flush=True)

if __name__=='__main__':main()
