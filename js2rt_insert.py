import os, sys, MySQLdb, json, re, time
from icecream import ic

def die(s):
	print(s)
	sys.exit(1)

def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )

def _byteify(data, ignore_dicts = False):
    if isinstance(data, unicode):
        return data.encode('utf-8')
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    return data	
	
def escapeString(s):
	return re.sub(r"['\r\n]", " ", s)

if os.name=="nt":
	timer = time.clock
else:
	timer = time.time
	
source = ''
batch_count = 1
index = 'wiki'
qport = 8306

i = 1
while (i<len(sys.argv)):
	arg = sys.argv[i]
	if arg=='--batch':
		i += 1
		batch_count = max (1, int(sys.argv[i]))
	elif arg=='--index':
		i += 1
		index = sys.argv[i]
	elif arg=='--port':
		i += 1
		qport = int(sys.argv[i])
	else:
		source = arg
	i += 1

if not source:
	die ( 'source MUST be specified' )

fp = open(source, 'r')
if not fp:
	die ( 'failed to open %s', source )

conn = MySQLdb.connect(host='127.0.0.1', user="root", passwd="", db="", port=qport)
cursor = conn.cursor ()

starttime = timer()
q_send = ''
q_sep = ''
q_got = 0
id = 1
total = 0
q_time = 0

for doc in iter(fp.readline, ''):
	decoded = json_loads_byteified(doc)
	names = ['id']
	values = [id]
	for k,v in decoded.iteritems():
		names.append(k)
		values.append(escapeString(v))

	q = ''
	if q_got==0:
		q = "REPLACE INTO " + index + " (" + ', '.join([str(x) for x in names]) + ") VALUES "

	q = q + " ('" + "', '".join([str(x) for x in values]) + "')"
	q_send = q_send + q_sep + q
	q_got = q_got + 1
	q_sep = ', '
	id = id + 1
	total = total + 1
	if q_got>=batch_count:
		q_start = timer()
		cursor.execute(q_send)
		rows = cursor.fetchall()
		q_send = ''
		q_sep = ''
		q_got = 0
		t = timer() - q_start
		q_time = q_time + t
		
if q_got>0:
	q_start = timer()
	cursor.execute(q)
	rows = cursor.fetchall()
	t = timer() - q_start
	q_time = q_time + t
	
fp.close()

t = timer() - starttime
print 'elapsed %.2f(%.2f) sec, %.1f qps, inserted %d, batch %d' % ( t, q_time, total/q_time, total, batch_count )
