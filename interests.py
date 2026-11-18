"""Deterministic topic filters and per-chat feedback; no LLM calls here."""
import json
import os
import re
from datetime import timedelta
import agent as a

TOPICS = {
 'claude_plugins': ('Claude 플러그인·스킬', [r'claude.{0,45}(plugin|skill|hook|extension)', r'(plugin|skill|hook).{0,45}claude', r'\.claude-plugin', r'\.claude/skills']),
 'mcp': ('MCP 서버·도구', [r'\bmcp\b', r'model context protocol']),
 'ai_coding': ('AI 코딩 도구', [r'coding agent', r'code assistant', r'claude code', r'\bcodex\b', r'\bcopilot\b']),
 'agents': ('AI 에이전트·자동화', [r'\bagentic\b', r'\bai agent', r'workflow automation', r'multi.agent']),
 'web_app': ('웹·앱 개발', [r'\breact\b', r'\bnext\.?js', r'\bfrontend\b', r'\bflutter\b', r'\bandroid\b', r'\bvue\b']),
 'data_ml': ('데이터·머신러닝', [r'machine learning', r'deep learning', r'\bpytorch\b', r'\bllm\b', r'data analysis', r'\bdataset']),
 'infra': ('개발 도구·인프라', [r'\bdocker\b', r'\bkubernetes\b', r'\bdevops\b', r'\bdatabase\b', r'\bterminal\b']),
 'other': ('기타·미분류', []),
 'security': ('보안·개인정보', [r'cybersecurity', r'vulnerability', r'\bencryption\b', r'\bsecurity\b', r'\bprivacy\b']),
}


def classify(text):
    return [key for key, (_, patterns) in TOPICS.items()
            if any(re.search(p, text, re.I | re.S) for p in patterns)] or ['other']


def setup(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS profiles(chat TEXT PRIMARY KEY, topics TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS documents(name TEXT PRIMARY KEY, body TEXT, tags TEXT);
    CREATE TABLE IF NOT EXISTS deliveries(chat TEXT, name TEXT, PRIMARY KEY(chat,name));
    CREATE TABLE IF NOT EXISTS votes(chat TEXT, name TEXT, value INTEGER, PRIMARY KEY(chat,name));
    ''')
    chats = set(filter(None, [os.getenv('TELEGRAM_CHAT_ID', '').strip()] +
                       [x.strip() for x in os.getenv('TELEGRAM_ALLOWED_CHAT_IDS','').split(',')]))
    for chat in chats:
        db.execute('INSERT OR IGNORE INTO profiles VALUES (?,?)', (chat, json.dumps(list(TOPICS))))
    db.commit()
    return chats


def send(chat, text, keyboard=None):
    payload = {'chat_id': chat, 'text': text, 'link_preview_options': {'is_disabled': True}}
    if keyboard:
        payload['reply_markup'] = {'inline_keyboard': keyboard}
    return a.telegram('sendMessage', payload)


def menu(db, chat):
    selected = json.loads(db.execute('SELECT topics FROM profiles WHERE chat=?', (chat,)).fetchone()[0])
    keyboard = [[{'text': ('✅ ' if key in selected else '⬜ ') + label,
                  'callback_data': 'topic:' + key}] for key, (label, _) in TOPICS.items()]
    send(chat, '받을 분야를 선택하세요(여러 개 가능). 선택 없음 = 알림 중지.\n'
         '/only claude_plugins → Claude 플러그인·스킬만\n'
         '/all → 전체 선택 /topics → 선택·해제 /status → 현황 /pause → 중지\n'
         '👍·👎는 선택 분야 내 순서에만 반영됩니다. 분야를 자동 추가하지 않습니다.', keyboard)


def apply_vote(db, chat, rid, value):
    row = db.execute('SELECT name FROM repos WHERE rowid=?', (rid,)).fetchone()
    if row and db.execute('SELECT 1 FROM deliveries WHERE chat=? AND name=?', (chat,row[0])).fetchone():
        db.execute('INSERT OR REPLACE INTO votes VALUES (?,?,?)', (chat,row[0],value))
        db.commit()
        return True
    return False


def poll(db):
    allowed = setup(db)
    offset = int(a.meta(db, 'telegram_offset') or 0)
    updates = a.telegram('getUpdates', {'offset': offset, 'timeout': 0,
                                       'allowed_updates': ['message', 'callback_query']})
    for update in updates:
        cb = update.get('callback_query')
        message = cb.get('message', {}) if cb else update.get('message', {})
        chat = str(message.get('chat', {}).get('id', ''))
        if chat in allowed and message.get('chat', {}).get('type') == 'private':
            if cb:
                data = cb.get('data', '')
                if data.startswith('topic:') and data[6:] in TOPICS:
                    # Absolute desired state is recorded per update to survive retries.
                    key = 'update:' + str(update['update_id'])
                    if not a.meta(db,key):
                        selected = set(json.loads(db.execute('SELECT topics FROM profiles WHERE chat=?',(chat,)).fetchone()[0]))
                        selected.symmetric_difference_update([data[6:]])
                        db.execute('UPDATE profiles SET topics=? WHERE chat=?',(json.dumps(sorted(selected)),chat))
                        a.setmeta(db,key,'done')
                    a.telegram('answerCallbackQuery', {'callback_query_id': cb['id'], 'text':'관심 분야 저장 완료'})
                    menu(db,chat)
                elif re.fullmatch(r'vote:\d+:(1|-1)', data):
                    _, rid, value = data.split(':')
                    apply_vote(db,chat,int(rid),int(value))
                    a.telegram('answerCallbackQuery', {'callback_query_id':cb['id'],'text':'피드백 저장 완료'})
            else:
                parts = message.get('text','').split()
                command, *args = parts or ['']
                command = command.split('@')[0]
                if command == '/only':
                    keys = set(' '.join(args).replace(',',' ').split())
                    if keys and keys <= TOPICS.keys():
                        db.execute('UPDATE profiles SET topics=? WHERE chat=?', (json.dumps(sorted(keys)),chat)); db.commit()
                        menu(db,chat)
                    else:
                        send(chat,'사용 가능한 코드: ' + ', '.join(TOPICS))
                elif command == '/all':
                    db.execute('UPDATE profiles SET topics=? WHERE chat=?',(json.dumps(list(TOPICS)),chat)); db.commit()
                    menu(db,chat)
                elif command == '/pause':
                    db.execute('UPDATE profiles SET topics=? WHERE chat=?',('[]',chat)); db.commit()
                    send(chat,'알림을 중지했습니다. /topics 로 다시 선택하세요.')
                elif command == '/status':
                    selected=json.loads(db.execute('SELECT topics FROM profiles WHERE chat=?',(chat,)).fetchone()[0])
                    send(chat,'선택: '+(', '.join(TOPICS[k][0] for k in selected) or '없음')+'\n매일 09:00 KST / 프로그램 개수 제한 없음 / Gemini 무료 한도 적용')
                else:
                    menu(db,chat)
        a.setmeta(db,'telegram_offset',str(update['update_id']+1))


def document(db,name,description):
    row=db.execute('SELECT body,tags FROM documents WHERE name=?',(name,)).fetchone()
    if row:
        return row[0],json.loads(row[1]) or ['other']
    headers={'Accept':'application/vnd.github.raw+json'}
    if os.getenv('GITHUB_TOKEN'):
        headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
    try:
        body=a.http('GET',f'https://api.github.com/repos/{name}/readme',headers=headers).text[:80000]
    except RuntimeError as e:
        if 'HTTP 404' not in str(e): raise
        body=''
    # Intro and path/manifest markers are useful; avoid matching arbitrary dependency mentions deep in README.
    tags=classify(name+'\n'+description+'\n'+body[:6000])
    db.execute('INSERT OR REPLACE INTO documents VALUES (?,?,?)',(name,body,json.dumps(tags)));db.commit()
    return body,tags


def score(db,chat,tags):
    result=0
    for value,raw in db.execute('SELECT v.value,d.tags FROM votes v JOIN documents d ON v.name=d.name WHERE v.chat=?',(chat,)):
        result += value*len(set(tags)&set(json.loads(raw)))
    return result


def digest(db,now):
    allowed=setup(db)
    items=a.parse_trending(a.http('GET','https://github.com/trending?since=daily',headers={'User-Agent':'personal-trending-watcher/2.0'}).text)
    if a.ingest(db,items,now):
        print('첫 기준 목록 저장: 요약/알림 없음. 텔레그램 /topics 로 분야 선택.'); return
    profiles=[(c,json.loads(t)) for c,t in db.execute('SELECT chat,topics FROM profiles') if c in allowed and json.loads(t)]
    if not profiles: return
    cutoff=(now-timedelta(days=7)).isoformat()
    rows=db.execute('SELECT rowid,name,description,summary FROM repos WHERE done=0 AND first_seen>=? ORDER BY first_seen,rowid',(cutoff,)).fetchall()
    candidates=[]
    for rid,name,desc,summary in rows:
        body,tags=document(db,name,desc)
        interested=[chat for chat,topics in profiles if set(topics)&set(tags) and not db.execute('SELECT 1 FROM deliveries WHERE chat=? AND name=?',(chat,name)).fetchone()]
        if interested:
            candidates.append((max(score(db,c,tags) for c in interested),rid,name,desc,summary,tags,interested))
    candidates.sort(key=lambda r:-r[0])
    for _,rid,name,desc,summary,tags,chats in candidates:
        summary=summary or a.summarize(db,now.date().isoformat(),name,desc)
        if summary is None: continue
        for chat in chats:
            send(chat,f'{name}\n{summary}\n분류: '+', '.join(TOPICS[t][0] for t in tags)+f'\nhttps://github.com/{name}',
                 [[{'text':'👍 관심 있어요','callback_data':f'vote:{rid}:1'},
                   {'text':'👎 덜 보고 싶어요','callback_data':f'vote:{rid}:-1'}]])
            db.execute('INSERT OR IGNORE INTO deliveries VALUES (?,?)',(chat,name))
            db.commit()
