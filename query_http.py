import os, time, sys, hashlib, json, requests
from urlparse import urlparse
from icecream import ic

def die(s):
	print (s)
	sys.exit ( 1 )

timer = time.time

if not sys.argv[1:]:
	print ("""Usage: query_http.py [OPTIONS] QUERIES.json
Options are:
--limit\t\tuse N first queries from source
--url\t\tadress:port/endpoint for requests
--dump\t\tdump additional data for each request doc,hash,time,query
--quiet\t\tsend requests only without any reports
--perf\t\tdisable ranking, result set got sort by attribute
""")
	sys.exit ( 0 )

url = '127.0.0.1:9200/wiki/_search'

limit = 0
qlog = ''
dumpdocs = False
dumpTime = False
dumpQuery = False
nohash = True
hashscore = True
quiet = False
qmode = 'mnt'

i = 1
while (i<len(sys.argv)):
	arg = sys.argv[i]
	if arg=='--limit':
		i += 1
		limit = int(sys.argv[i])
	elif arg=='--url':
		i += 1
		url = sys.argv[i]
	elif arg=='--dump':
		i += 1
		if sys.argv[i].find('doc')!=-1:
			dumpdocs = True
		if sys.argv[i].find('hash')!=-1:
			nohash = False
		if sys.argv[i].find('time')!=-1:
			dumpTime = True
		if sys.argv[i].find('query')!=-1:
			dumpQuery = True
	elif arg=='--quiet':
		quiet = True
	elif arg=='--perf':
		nohash = True
		hashscore = False
	elif arg=='--noscore':
		hashscore = False
	elif arg=='--qmode':
		i += 1
		qmode = sys.argv[i]
	elif arg[0:1]=='-':
		die ( 'unknown argument %s' % sys.argv[i] )
	else:
		if qlog=='':
			qlog = arg
		else:
			die ( 'only one query log can be specified' )
	i += 1

if not qlog:
	die ( 'query log MUST be specified' )

fp = open ( qlog, 'r' )
if not fp:
	die ( 'failed to open %s', sys.argv[1:] )
queries = json.load(fp)["queries"]
fp.close()

if limit:
	queries = queries[0:limit]

# clear cache	
ulist = urlparse(url)
res = requests.get(ulist.scheme+'://'+ulist.netloc+'/_cache/clear')
if res.status_code!=200:
	ic(res.status_code, res.json())
	
qhash = ''
starttime = timer()
tm = 0
fullhash = hashlib.md5()
qid = 0
headers = {'Content-Type': 'application/json'}
for q in queries:

	q_full = {"query":q}
	if nohash and not hashscore:
		q_full["sort"] = ["pmid"]
		q_full["track_scores"] = False
	
	start_req = timer()
	res = requests.post(url, data=json.dumps(q_full), headers=headers)
	tm_cur = timer() - start_req
	tm_req = int( tm_cur * 1000.0 )
	
	#ic(res.status_code, res.json())
	reply = res.json()
	
	docs = "0: "
	total = 0
	if 'hits' in reply and 'total' in reply['hits']:
		docs = str(reply['hits']['total']) + ': '
		
	if not nohash or dumpdocs:
		ids = hashlib.md5()
		ids.update ( 'got %d: ' % qid )
		if 'hits' in reply and 'hits' in reply['hits']:
			for match in reply['hits']['hits']:
				docid = str(match['_id'])
				ids.update ( docid )
				ids.update ( ' ' )
				if dumpdocs:
					docs = docs + docid + ' '
				if hashscore:
					ids.update ( str(match['_score']) )
					ids.update ( ' ' )
		ids.update ( '\n' )

		qhash = ids.hexdigest()
		fullhash.update ( qhash )

	if dumpTime and reply.has_key('took'):
		total = reply['took']

	if nohash:
		qhash = ''
		
	if not quiet:
		print ('%d, code %d, %d(%d) msec, hash %s, docs %s, query %s' % ( qid, res.status_code, tm_req, total, qhash, docs, q if dumpQuery else ''))
	
	tm = tm + tm_cur
	qid += 1


if not nohash:
	print ('hash %s' % fullhash.hexdigest())

t = timer() - starttime
print ('elapsed %.3f(%.3f) sec, %.1f qps' % ( t, tm, len(queries)/t ))
