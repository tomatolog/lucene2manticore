import os, sys, time, datetime, wikiclean, re, json


def die(s):
	print(s)
	sys.exit(1)

def doc_dump (index_name, type_name, docid, ts, title, body, maxlen):

	if maxlen>0 and len(body)>maxlen:
		nonword = body.find(' ', maxlen)
		if nonword!=-1:
			body = body[0:nonword]

	meta_data = {"index": { "_index": index_name, "_type": type_name, "_id": docid } }			
	print(json.dumps(meta_data, ensure_ascii=False))
	doc_data = {"name": title, "timestamp": ts, "pmid": ts, "body": body}
	print(json.dumps(doc_data, ensure_ascii=False))
	
if not sys.argv[1:]:
	print ("""Usage: lucene2bulk.py [OPTIONS] docs.tsv
Options are:
--docs\t\tprocess only first N documents (default all documents)
--maxlen\tuse first N bytes of document (default whole document)
--index\t\tindex name
--type\t\ttype of documents
""")
	sys.exit ( 0 )
	
source = ''
docs = 0
maxlen = 0
index_name = 'wiki'
type_name = 'articles'

i = 1
while (i<len(sys.argv)):
	arg = sys.argv[i]
	if arg=='--docs':
		i += 1
		docs = int(sys.argv[i])
	elif arg=='--maxlen':
		i += 1
		maxlen = int(sys.argv[i])
	elif arg=='--index':
		i += 1
		index_name = sys.argv[i]
	elif arg=='--type':
		i += 1
		type_name = sys.argv[i]
	else:
		source = arg
	i += 1

if not source:
	die ( 'source MUST be specified' )

fp = open(source, 'r')
if not fp:
	die ( 'failed to open %s', source )

docid = 0
title = ''
timestamp = 0
text = ''
fp.readline() # skip header with column names
for doc in iter(fp.readline, ''):
	columns = doc.rstrip('\n').split('\t')
	if title==columns[0]:
		if len(columns)==3:
			text = text + ' ' + re.sub('\s+',' ', columns[2])
	else:
		if len(title):
			text = re.sub('\s+',' ', wikiclean.clean(text))
			
			doc_dump(index_name, type_name, docid, timestamp, title, text, maxlen)
			#sys.stdout.flush()
			
		if docs!=0 and docid>=docs:
			title = ''
			break
		
		docid = docid + 1
		title = columns[0]
		timestamp = int(time.mktime(datetime.datetime.strptime(columns[1], "%d-%b-%Y %H:%M:%S.%f").timetuple()))
		text = columns[2]

fp.close()

if len(title)>0:
	doc_dump(index_name, type_name, docid, timestamp, title, text, maxlen)
	
# corpora option "includes-action-and-meta-data" : True
# format	
# {"index": {"_index": "wiki", "_type": "articles"}}
#{"name":"20_Century_Br_Hist_2015_Sep_27_26(3)_450-476","journal":"20 Century Br Hist","date":"2015 Sep 27","volume":"26(3)","issue":"450-476","accession":"PMC4804230","timestamp":"2016-03-24 20:08:28","pmid":"","body":"\n==== Front\n20 Century"}	