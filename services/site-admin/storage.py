"""Bounded DynamoDB access, atomic deduplication and separate retention domains."""
import os,time,json
from datetime import datetime,timedelta,timezone
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from contracts import Invalid

class Store:
    def __init__(self):
        db=boto3.resource('dynamodb')
        self.tables={name:db.Table(os.environ[name.upper()+'_TABLE']) for name in ('events','inquiries','audit','sessions')}
    def get(self,table,pk,sk='0'):
        row=self.tables[table].get_item(Key={'pk':pk,'sk':sk},ConsistentRead=True).get('Item')
        return row if row and row.get('ttl',0)>int(time.time()) else None
    def put(self,table,row,unique=False):
        try:
            self.tables[table].put_item(Item=row,**({'ConditionExpression':'attribute_not_exists(pk)'} if unique else {}));return True
        except ClientError as e:
            if e.response['Error']['Code']=='ConditionalCheckFailedException':return False
            raise
    def delete(self,table,pk,sk='0'):
        self.tables[table].delete_item(Key={'pk':pk,'sk':sk})
    def consume(self,pk):
        row=self.tables['sessions'].delete_item(Key={'pk':pk,'sk':'0'},ReturnValues='ALL_OLD').get('Attributes')
        return row if row and row.get('ttl',0)>int(time.time()) else None
    def rate(self,key,limit,seconds):
        now=int(time.time());bucket=now//seconds
        try:
            self.tables['sessions'].update_item(Key={'pk':f'rate#{key}#{bucket}','sk':'0'},UpdateExpression='SET #n=if_not_exists(#n,:zero)+:one, #ttl=:ttl',ConditionExpression='attribute_not_exists(#n) OR #n < :limit',ExpressionAttributeNames={'#n':'n','#ttl':'ttl'},ExpressionAttributeValues={':zero':0,':one':1,':limit':limit,':ttl':(bucket+2)*seconds});return True
        except ClientError as e:
            if e.response['Error']['Code']=='ConditionalCheckFailedException':return False
            raise
    def query(self,table,pk,limit=2000,byte_limit=1500000):
        result=[];start=None;scanned=0;size=0
        while len(result)<limit and scanned<limit:
            response=self.tables[table].query(KeyConditionExpression=Key('pk').eq(pk),Limit=min(500,limit-scanned),ConsistentRead=True,**({'ExclusiveStartKey':start} if start else {}))
            scanned+=response.get('ScannedCount',len(response['Items']))
            for row in response['Items']:
                if row.get('ttl',0)<=int(time.time()):continue
                size+=len(json.dumps(row,default=str).encode())
                if size>byte_limit:return result,True
                result.append(row)
            start=response.get('LastEvaluatedKey')
            if not start:break
        return result,bool(start)
    def events(self,start,end,limit=20000):
        # Persisted retention days produce Decimal epoch bounds. Convert only
        # the whole-second timestamps required by datetime, not measured values.
        result=[];day=datetime.fromtimestamp(int(start),timezone.utc).date();last=datetime.fromtimestamp(int(end-1),timezone.utc).date();partial=False
        while day<=last:
            if len(result)>=limit:partial=True;break
            rows,cut=self.query('events',str(day),limit-len(result));partial|=cut
            result.extend(r for r in rows if start<=r['at']<end);day+=timedelta(days=1)
        return result,partial
    def save_event(self,row,retention):
        now=int(time.time());day=datetime.fromtimestamp(row['at'],timezone.utc).date().isoformat()
        # Event ID is global, not scoped by client-supplied date or page.
        marker={'pk':'event#'+row['id'],'sk':'0','ttl':now+172800}
        stored=dict(row,pk=day,sk=row['id'],ttl=row['at']+retention*86400)
        if self.get('sessions',marker['pk']):return False
        pagekey='page#'+row['page']
        page=self.get('sessions',pagekey)
        actions=[{'Put':{'TableName':self.tables['sessions'].name,'Item':marker,'ConditionExpression':'attribute_not_exists(pk)'}},{'Put':{'TableName':self.tables['events'].name,'Item':stored,'ConditionExpression':'attribute_not_exists(pk)'}}]
        if row['name']=='pageview':
            if page:raise Invalid('Page instance already registered')
            state=dict(pk=pagekey,sk='0',visitor=row['visitor'],session=row['session'],path=row['path'],at=row['at'],total=0,ttl=now+172800)
            actions.append({'Put':{'TableName':self.tables['sessions'].name,'Item':state,'ConditionExpression':'attribute_not_exists(pk)'}})
        else:
            if not page or any(page[k]!=row[k] for k in ('visitor','session','path')) or row['at']<page['at']:raise Invalid('Page instance unavailable or mismatched')
            if row['name']=='engagement':
                budget=min(14400000,(row['at']-int(page['at'])+5)*1000)
                actions.append({'Update':{'TableName':self.tables['sessions'].name,'Key':{'pk':pagekey,'sk':'0'},'UpdateExpression':'SET #total=#total+:value','ConditionExpression':'#total <= :remaining','ExpressionAttributeNames':{'#total':'total'},'ExpressionAttributeValues':{':value':row['value'],':remaining':budget-row['value']}}})
        try:
            self.tables['events'].meta.client.transact_write_items(TransactItems=actions);return True
        except ClientError as e:
            if e.response['Error']['Code']=='TransactionCanceledException':
                if self.get('sessions',marker['pk']):return False
                raise Invalid('Measurement exceeds page bounds or conflicts with a concurrent update')
            raise
    def audit(self,action,subject,owner):
        import uuid
        now=int(time.time());self.put('audit',dict(pk='audit',sk=f'{now}#{uuid.uuid4()}',at=now,action=action,subject=subject,owner=owner,ttl=now+365*86400))
