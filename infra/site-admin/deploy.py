"""Provision the isolated site service, then append an uncached API origin to the existing CDN.
Requires an explicitly authorized provisioning profile. Never reads GitHub deployment secrets.
"""
import argparse,copy,hashlib,json,os,subprocess,sys,tempfile,time,zipfile
from pathlib import Path
import boto3
ROOT=Path(__file__).resolve().parents[2]

def connected_config(config,outputs,secret):
    c=copy.deepcopy(config)
    if 'khalidshams.com' not in c.get('Aliases',{}).get('Items',[]):raise ValueError('Distribution does not serve khalidshams.com')
    origin_id='shams-site-admin-api'
    origins=c['Origins']['Items'];existing=[o for o in origins if o['Id']==origin_id]
    api={'Id':origin_id,'DomainName':outputs['ApiHost'],'OriginPath':'/prod','CustomHeaders':{'Quantity':1,'Items':[{'HeaderName':'X-Site-Origin','HeaderValue':secret}]},'CustomOriginConfig':{'HTTPPort':80,'HTTPSPort':443,'OriginProtocolPolicy':'https-only','OriginSslProtocols':{'Quantity':1,'Items':['TLSv1.2']},'OriginReadTimeout':30,'OriginKeepaliveTimeout':5},'ConnectionAttempts':2,'ConnectionTimeout':10}
    if existing:origins[origins.index(existing[0])]=api
    else:origins.append(api)
    c['Origins']['Quantity']=len(origins)
    behaviors=c.setdefault('CacheBehaviors',{'Quantity':0}).setdefault('Items',[])
    routes=[b for b in behaviors if b['PathPattern'] in ('/api/*','api/*')]
    if any(b['TargetOriginId']!=origin_id for b in routes):raise ValueError('An existing API behavior belongs to another service; inspect before changing')
    behavior={'PathPattern':'/api/*','TargetOriginId':origin_id,'ViewerProtocolPolicy':'https-only','AllowedMethods':{'Quantity':7,'Items':['GET','HEAD','OPTIONS','PUT','PATCH','POST','DELETE'],'CachedMethods':{'Quantity':2,'Items':['GET','HEAD']}},'TrustedSigners':{'Enabled':False,'Quantity':0},'TrustedKeyGroups':{'Enabled':False,'Quantity':0},'Compress':True,'CachePolicyId':outputs['NoCachePolicyId'],'OriginRequestPolicyId':outputs['OriginRequestPolicyId'],'SmoothStreaming':False,'FieldLevelEncryptionId':'','LambdaFunctionAssociations':{'Quantity':0},'FunctionAssociations':{'Quantity':0}}
    behaviors[:]=[behavior]+[b for b in behaviors if b not in routes];c['CacheBehaviors']['Quantity']=len(behaviors)
    assert c['DefaultCacheBehavior']==config['DefaultCacheBehavior']
    return c

def private_json(path,value):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(value,out,indent=2)

def main():
    p=argparse.ArgumentParser();p.add_argument('--profile');p.add_argument('--region',default='us-east-1');p.add_argument('--stack',default='shams-site-admin');p.add_argument('--distribution',default='E14OT21V7ATYP1');p.add_argument('--owner-email',required=True);p.add_argument('--domain-prefix',required=True);p.add_argument('--deploy',action='store_true');p.add_argument('--connect',action='store_true');p.add_argument('--evidence-dir',required=True);a=p.parse_args()
    session=boto3.Session(profile_name=a.profile,region_name=a.region);sts=session.client('sts').get_caller_identity();cf=session.client('cloudfront');original=cf.get_distribution_config(Id=a.distribution)
    if 'khalidshams.com' not in original['DistributionConfig'].get('Aliases',{}).get('Items',[]):raise SystemExit('Wrong site distribution')
    evidence=Path(a.evidence_dir).expanduser().resolve();evidence.mkdir(parents=True,exist_ok=True);os.chmod(evidence,0o700)
    stamp=str(int(time.time()));private_json(evidence/('cloudfront-before-'+stamp+'.json'),original)
    print(json.dumps({'account':sts['Account'],'distribution':a.distribution,'legacy_cloudfront_logging':original['DistributionConfig'].get('Logging',{}),'changes':'New isolated Cognito, Lambda role, API, four private DynamoDB tables, origin secret, no-cache policies. Existing default CDN behavior preserved.','execute':a.deploy,'connect_api':a.connect},indent=2))
    if not a.deploy:return
    s3=session.client('s3');bucket=f'shams-admin-artifacts-{sts["Account"]}-{a.region}'
    try:s3.head_bucket(Bucket=bucket)
    except s3.exceptions.ClientError as error:
        if error.response['Error']['Code'] not in ('404','NoSuchBucket','NotFound'):raise
        s3.create_bucket(Bucket=bucket,**({'CreateBucketConfiguration':{'LocationConstraint':a.region}} if a.region!='us-east-1' else {}))
    s3.put_public_access_block(Bucket=bucket,PublicAccessBlockConfiguration={k:True for k in ('BlockPublicAcls','IgnorePublicAcls','BlockPublicPolicy','RestrictPublicBuckets')})
    s3.put_bucket_encryption(Bucket=bucket,ServerSideEncryptionConfiguration={'Rules':[{'ApplyServerSideEncryptionByDefault':{'SSEAlgorithm':'AES256'}}]})
    s3.put_bucket_versioning(Bucket=bucket,VersioningConfiguration={'Status':'Enabled'})
    s3.put_bucket_tagging(Bucket=bucket,Tagging={'TagSet':[{'Key':'Project','Value':'khalidshams.com-site-admin'}]})
    with tempfile.TemporaryDirectory(prefix='shams-admin-') as tmp:
        build=Path(tmp)/'package';build.mkdir()
        subprocess.run([sys.executable,'-m','pip','install','--requirement',str(ROOT/'services/site-admin/requirements.txt'),'--target',str(build),'--platform','manylinux2014_aarch64','--python-version','3.12','--implementation','cp','--only-binary=:all:','--quiet'],check=True)
        for file in (ROOT/'services/site-admin').iterdir():
            if file.suffix in ('.py','.json'):(build/file.name).write_bytes(file.read_bytes())
        archive=Path(tmp)/'lambda.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for file in build.rglob('*'):
                if file.is_file() and '__pycache__' not in file.parts:z.write(file,str(file.relative_to(build)))
        digest=hashlib.sha256(archive.read_bytes()).hexdigest();key='releases/'+digest+'.zip';s3.upload_file(str(archive),bucket,key)
    template=json.loads((ROOT/'infra/site-admin/template.json').read_text());template['Resources']['App']['Properties']['CodeUri']={'Bucket':bucket,'Key':key}
    cloud=session.client('cloudformation');name='site-admin-'+stamp
    try:cloud.describe_stacks(StackName=a.stack);kind='UPDATE'
    except cloud.exceptions.ClientError as error:
        if 'does not exist' not in error.response['Error'].get('Message',''):raise
        kind='CREATE'
    cloud.create_change_set(StackName=a.stack,ChangeSetName=name,ChangeSetType=kind,TemplateBody=json.dumps(template),Capabilities=['CAPABILITY_IAM','CAPABILITY_AUTO_EXPAND'],Parameters=[{'ParameterKey':'OwnerEmail','ParameterValue':a.owner_email},{'ParameterKey':'AuthDomainPrefix','ParameterValue':a.domain_prefix}],Tags=[{'Key':'Project','Value':'khalidshams.com-site-admin'}])
    try:cloud.get_waiter('change_set_create_complete').wait(StackName=a.stack,ChangeSetName=name)
    except Exception:
        change=cloud.describe_change_set(StackName=a.stack,ChangeSetName=name)
        if "didn't contain changes" not in change.get('StatusReason',''):raise
    else:
        cloud.execute_change_set(StackName=a.stack,ChangeSetName=name)
        cloud.get_waiter('stack_create_complete' if kind=='CREATE' else 'stack_update_complete').wait(StackName=a.stack)
    stack=cloud.describe_stacks(StackName=a.stack)['Stacks'][0];outputs={x['OutputKey']:x['OutputValue'] for x in stack['Outputs']};private_json(evidence/('stack-'+stamp+'.json'),{'status':stack['StackStatus'],'outputs':outputs,'artifact_sha256':digest})
    if a.connect:
        # Fresh ETag: never overwrite a concurrent distribution change.
        original=cf.get_distribution_config(Id=a.distribution)
        secret=session.client('secretsmanager').get_secret_value(SecretId=outputs['OriginSecretArn'])['SecretString']
        config=connected_config(original['DistributionConfig'],outputs,secret)
        cf.update_distribution(Id=a.distribution,IfMatch=original['ETag'],DistributionConfig=config)
        cf.get_waiter('distribution_deployed').wait(Id=a.distribution)
        updated=cf.get_distribution_config(Id=a.distribution)['DistributionConfig'];api=next(b for b in updated['CacheBehaviors']['Items'] if b['PathPattern']=='/api/*')
        assert api['CachePolicyId']==outputs['NoCachePolicyId'] and api.get('FunctionAssociations',{}).get('Quantity',0)==0
        cf.create_invalidation(DistributionId=a.distribution,InvalidationBatch={'Paths':{'Quantity':1,'Items':['/api/*']},'CallerReference':'shams-admin-'+stamp})
        print('API connected with caching disabled and no URL rewrite function.')
    print('Stack ready. Complete the secure Cognito owner invitation and MFA, then run live acceptance checks. No owner password or MFA seed is printed.')
if __name__=='__main__':main()
