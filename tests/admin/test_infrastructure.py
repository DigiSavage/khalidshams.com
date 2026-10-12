import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];spec=importlib.util.spec_from_file_location('deploy',ROOT/'infra/site-admin/deploy.py');deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)
class InfrastructureTests(unittest.TestCase):
 def test_api_routing_preserves_site_and_disables_rewrite(self):
  source={'Aliases':{'Items':['khalidshams.com']},'Origins':{'Quantity':1,'Items':[{'Id':'site','DomainName':'site.s3.amazonaws.com'}]},'DefaultCacheBehavior':{'TargetOriginId':'site','FunctionAssociations':{'Quantity':1,'Items':[{'FunctionARN':'rewrite','EventType':'viewer-request'}]}},'CacheBehaviors':{'Quantity':1,'Items':[{'PathPattern':'/static/*','TargetOriginId':'site'}]},'Logging':{'Enabled':False}}
  original=copy.deepcopy(source);outputs={'ApiHost':'api.execute-api.us-east-1.amazonaws.com','NoCachePolicyId':'zero','OriginRequestPolicyId':'cookies'}
  result=deploy.connected_config(source,outputs,'fixture-secret');self.assertEqual(source,original);self.assertEqual(result['DefaultCacheBehavior'],source['DefaultCacheBehavior']);self.assertEqual(result['CacheBehaviors']['Items'][0]['FunctionAssociations']['Quantity'],0);self.assertEqual(result['CacheBehaviors']['Items'][0]['CachePolicyId'],'zero');self.assertEqual(result['Origins']['Items'][-1]['OriginPath'],'/prod');self.assertEqual(result['Logging'],source['Logging']);self.assertEqual(deploy.connected_config(result,outputs,'fixture-secret'),result)
  result['CacheBehaviors']['Items'][0]['TargetOriginId']='other-service'
  with self.assertRaises(ValueError):deploy.connected_config(result,outputs,'fixture-secret')
 def test_auth_and_private_storage_template(self):
  t=json.loads((ROOT/'infra/site-admin/template.json').read_text())['Resources'];pool=t['OwnerPool']['Properties'];self.assertEqual(pool['MfaConfiguration'],'ON');self.assertTrue(pool['AdminCreateUserConfig']['AllowAdminCreateUserOnly']);self.assertFalse(t['OwnerClient']['Properties']['GenerateSecret'])
  for n in ('Events','Inquiries','Audit','Sessions'):self.assertTrue(t[n]['Properties']['SSESpecification']['SSEEnabled']);self.assertTrue(t[n]['Properties']['TimeToLiveSpecification']['Enabled'])
  self.assertEqual(t['NoCache']['Properties']['CachePolicyConfig']['MaxTTL'],0);self.assertEqual(t['AppLogs']['Properties']['RetentionInDays'],14)
