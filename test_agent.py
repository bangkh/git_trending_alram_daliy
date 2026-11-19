import unittest
from unittest.mock import patch
from datetime import datetime,timedelta
import agent as a
import interests as i

class Tests(unittest.TestCase):
    def setUp(self):
        self.db=a.connect(':memory:')
        self.env=patch.dict('os.environ',{'TELEGRAM_CHAT_ID':'1','TELEGRAM_ALLOWED_CHAT_IDS':'2'})
        self.env.start();i.setup(self.db)
        self.now=datetime(2026,11,18,9,tzinfo=a.TZ)
    def tearDown(self):
        self.db.close();self.env.stop()
    def test_unlimited_distinct_repos_and_failure_retry_guard(self):
        for n in range(40):self.assertIsNotNone(a.reserve(self.db,'2026-11-18',str(n)))
        self.assertIsNone(a.reserve(self.db,'2026-11-18','1'))
        self.assertIsNotNone(a.reserve(self.db,'2026-11-19','1'))
    def test_default_all_and_existing_choices_preserved(self):
        import json
        selected=json.loads(self.db.execute('select topics from profiles where chat="1"').fetchone()[0])
        self.assertEqual(set(selected),set(i.TOPICS))
        self.db.execute('update profiles set topics=? where chat=?', ('[]','1'))
        i.setup(self.db)
        self.assertEqual(self.db.execute('select topics from profiles where chat="1"').fetchone()[0],'[]')
    def test_uncategorized_included(self):
        self.assertEqual(i.classify('A collection of poems'),['other'])
    def test_all_command(self):
        import json
        self.db.execute('update profiles set topics=? where chat=?', ('[]','1'))
        update={'update_id':10,'message':{'chat':{'id':1,'type':'private'},'text':'/all'}}
        with patch.object(a,'telegram',return_value=[update]),patch.object(i,'send'):i.poll(self.db)
        self.assertEqual(set(json.loads(self.db.execute('select topics from profiles where chat="1"').fetchone()[0])),set(i.TOPICS))
    def test_more_than_three_deliveries(self):
        a.ingest(self.db,[('a/old','')],self.now)
        a.ingest(self.db,[(f'a/new{n}','') for n in range(8)],self.now)
        self.db.execute('update repos set summary=? where done=0',('cached',))
        html='<article class="Box-row"><h2><a href="/a/old">x</a></h2></article>'
        with patch.object(a,'http',return_value=type('R',(),{'text':html})()),patch.object(i,'document',return_value=('', ['other'])),patch.object(i,'send') as send:
            i.digest(self.db,self.now)
            self.assertEqual(send.call_count,20)
            i.digest(self.db,self.now)
            self.assertEqual(send.call_count,20)
    def test_first_run_migration_and_daily_notice(self):
        a.ingest(self.db,[('a/b','')],self.now-timedelta(days=10))
        self.db.execute('update repos set done=1')
        html='<article class="Box-row"><h2><a href="/a/b">x</a></h2></article>'
        with patch.object(a,'http',return_value=type('R',(),{'text':html})()),patch.object(i,'document',return_value=('', ['other'])),patch.object(a,'summarize',return_value='summary') as ai,patch.object(i,'send') as send:
            i.digest(self.db,self.now)
            ai.assert_called_once()
            self.assertEqual(self.db.execute('select count(*) from deliveries').fetchone()[0],2)
            first=send.call_count
            i.digest(self.db,self.now)
            self.assertEqual(send.call_count,first)
            i.digest(self.db,self.now+timedelta(days=1))
            self.assertEqual(send.call_count,first+2)
            self.assertIn('새로 보낼 저장소가 없습니다',send.call_args.args[1])
    def test_pending_is_not_empty(self):
        html='<article class="Box-row"><h2><a href="/a/b">x</a></h2></article>'
        with patch.object(a,'http',return_value=type('R',(),{'text':html})()),patch.object(i,'document',return_value=('', ['other'])),patch.object(a,'summarize',side_effect=RuntimeError('HTTP 403')),patch.object(i,'send') as send:
            i.digest(self.db,self.now)
            self.assertIn('요약 오류',send.call_args.args[1])
            self.assertEqual(self.db.execute('select count(*) from deliveries').fetchone()[0],0)
    def test_paused_no_notice(self):
        self.db.execute('update profiles set topics=?',('[]',))
        html='<article class="Box-row"><h2><a href="/a/b">x</a></h2></article>'
        with patch.object(a,'http',return_value=type('R',(),{'text':html})()),patch.object(i,'send') as send:
            i.digest(self.db,self.now)
            send.assert_not_called()
    def test_old_model_failure_does_not_block_new_model(self):
        self.db.execute('INSERT INTO calls(week,name,model) VALUES (?,?,?)',('2026-11-18','a/b','gemini-2.5-flash-lite'))
        self.db.commit()
        self.assertIsNotNone(a.reserve(self.db,'2026-11-18','a/b'))
        self.assertIsNone(a.reserve(self.db,'2026-11-18','a/b'))
    def test_daily_boundary(self):
        _,old=a.due(self.now-timedelta(minutes=1),None)
        self.assertTrue(a.due(self.now,old)[0])
        self.assertFalse(a.due(self.now,a.due(self.now,None)[1])[0])
        self.assertTrue(a.due(self.now+timedelta(days=1),a.due(self.now,None)[1])[0])
    def test_strict_claude(self):
        self.assertIn('claude_plugins',i.classify('Claude Code plugin marketplace'))
        self.assertNotIn('claude_plugins',i.classify('MCP server for Claude'))
        self.assertNotIn('claude_plugins',i.classify('Claude API wrapper'))
    def test_first_baseline(self):
        self.assertTrue(a.ingest(self.db,[('a/b','')],self.now))
        self.assertFalse(a.ingest(self.db,[('a/b',''),('a/c','')],self.now))
        self.assertEqual(self.db.execute('select name from repos where done=0').fetchall(),[('a/b',),('a/c',)])
    def test_vote_idempotent_and_isolated(self):
        a.ingest(self.db,[('a/b','')],self.now)
        self.db.execute('insert into deliveries values (?,?)',('1','a/b'))
        self.db.execute('insert into documents values (?,?,?)',('a/b','','["mcp"]'))
        rid=self.db.execute('select rowid from repos').fetchone()[0]
        for _ in range(2):i.apply_vote(self.db,'1',rid,1)
        self.assertEqual(i.score(self.db,'1',['mcp']),1)
        self.assertEqual(i.score(self.db,'2',['mcp']),0)
        i.apply_vote(self.db,'1',rid,-1)
        self.assertEqual(i.score(self.db,'1',['mcp']),-1)
    def test_unauthorized_update(self):
        update={'update_id':1,'message':{'chat':{'id':99,'type':'private'},'text':'/only mcp'}}
        with patch.object(a,'telegram',return_value=[update]) as api:i.poll(self.db)
        self.assertEqual(api.call_count,1)
        self.assertEqual(self.db.execute('select count(*) from profiles').fetchone()[0],2)
    def test_unmatched_no_ai_or_send(self):
        a.ingest(self.db,[('a/old','')],self.now)
        self.db.execute('update profiles set topics=?', ('[]',))
        self.db.execute('update profiles set topics=? where chat=?',('["claude_plugins"]','1'))
        html='<article class="Box-row"><h2><a href="/a/new">x</a></h2></article>'
        with patch.object(a,'http',return_value=type('R',(),{'text':html})()),patch.object(i,'document',return_value=('', ['web_app'])),patch.object(a,'summarize') as ai,patch.object(i,'send') as send:
            i.digest(self.db,self.now);ai.assert_not_called()
            self.assertIn('새로 보낼 저장소가 없습니다',send.call_args.args[1])
    def test_cached_delivery_failure(self):
        a.ingest(self.db,[('a/old','')],self.now);a.ingest(self.db,[('a/new','')],self.now)
        self.db.execute('update profiles set topics=? where chat=?',('["mcp"]','1'))
        self.db.execute('update repos set done=1 where name=?',('a/old',))
        self.db.execute('update repos set summary=? where name=?',('cached','a/new'))
        html='<article class="Box-row"><h2><a href="/a/new">x</a></h2></article>'
        with patch.object(a,'http',return_value=type('R',(),{'text':html})()),patch.object(i,'document',return_value=('', ['mcp'])),patch.object(a,'summarize') as ai,patch.object(i,'send',side_effect=RuntimeError('fail')):
            with self.assertRaises(RuntimeError):i.digest(self.db,self.now)
            ai.assert_not_called()
        self.assertEqual(self.db.execute('select count(*) from deliveries').fetchone()[0],0)
    def test_parser_fails_closed(self):
        with self.assertRaises(RuntimeError):a.parse_trending('<html>blocked</html>')

class GeminiTests(unittest.TestCase):
    def setUp(self):
        self.db=a.connect(':memory:')
        a.ingest(self.db,[('a/b','')],datetime.now(a.TZ))
        self.env=patch.dict('os.environ',{'GEMINI_API_KEY':'fake-key','GEMINI_FREE_TIER_CONFIRMED':'yes'})
        self.env.start()
    def tearDown(self):
        self.db.close();self.env.stop()
    def test_gemini_request_and_cache(self):
        data={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'목적: 테스트'}]}}],
              'usageMetadata':{'promptTokenCount':100,'candidatesTokenCount':20}}
        with patch.object(i,'document',return_value=('README',[])), patch.object(a,'http') as http:
            http.return_value.json.return_value=data
            self.assertEqual(a.summarize(self.db,'2026-11-18','a/b',''), '목적: 테스트')
            args,kw=http.call_args
            self.assertIn('gemini-3.5-flash-lite:generateContent',args[1])
            self.assertEqual(kw['json']['generationConfig']['thinkingConfig'],{'thinkingLevel':'MINIMAL'})
            self.assertNotIn('fake-key',args[1])
            self.assertEqual(kw['json']['generationConfig']['maxOutputTokens'],1024)
        self.assertEqual(self.db.execute('select summary from repos').fetchone()[0],'목적: 테스트')
    def test_quota_stops_today_without_fallback(self):
        with patch.object(i,'document',return_value=('',[])),patch.object(a,'http',side_effect=RuntimeError('HTTP 429')) as http:
            self.assertIsNone(a.summarize(self.db,'2026-11-18','a/b',''))
            self.assertIsNone(a.summarize(self.db,'2026-11-18','a/b',''))
            self.assertEqual(http.call_count,1)
            self.assertIsNone(a.summarize(self.db,'2026-11-19','a/b',''))
            self.assertEqual(http.call_count,2)
    def test_incomplete_not_cached(self):
        with patch.object(i,'document',return_value=('',[])),patch.object(a,'http') as http:
            http.return_value.json.return_value={'candidates':[{'finishReason':'MAX_TOKENS','content':{'parts':[{'text':'partial'}]}}]}
            with self.assertRaises(RuntimeError):a.summarize(self.db,'2026-11-18','a/b','')
        self.assertIsNone(self.db.execute('select summary from repos').fetchone()[0])
    def test_requires_free_tier_acknowledgment(self):
        with patch.dict('os.environ',{'GEMINI_FREE_TIER_CONFIRMED':'no'}),patch.object(a,'http') as http:
            with self.assertRaises(RuntimeError):a.summarize(self.db,'2026-11-18','a/b','')
            http.assert_not_called()

if __name__=='__main__':unittest.main()

