"""Commit only candidate artifacts and summaries; never commit raw FEM work."""
from pathlib import Path
import base64,os,subprocess
ROOT=Path.cwd()
def git(*a,auth=False):
    env=os.environ.copy()
    if auth:
        auth64=base64.b64encode(('x-access-token:'+env['GH_TOKEN']).encode()).decode()
        env.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',GIT_CONFIG_VALUE_0='AUTHORIZATION: basic '+auth64)
    return subprocess.check_output(['git',*a],text=True,env=env).strip()
def main():
    paths=[]
    for folder in ['models/L2_r4','reports/l2_r4','views/l2_r4','handoff/l2_r4']:
        if (ROOT/folder).exists():paths.append(folder)
    if not paths:return
    git('config','user.name','github-actions[bot]');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    git('add','--',*paths)
    if not git('diff','--cached','--name-only'):return
    parent=git('rev-parse','HEAD')
    git('commit','-m','Record L2-r4 candidate outputs and actual validation status')
    # A concurrent source update must never be overwritten.
    expected=os.getenv('R4_TARGET_BRANCH','l2-r4-build')
    head=git('ls-remote','origin','refs/heads/'+expected).split()[0]
    target=expected if head==parent else 'l2-r4-result-'+os.environ['GITHUB_RUN_ID']
    git('push','origin','HEAD:refs/heads/'+target,auth=True)
    print('CHECKPOINT',target,git('rev-parse','HEAD'))
if __name__=='__main__':main()
