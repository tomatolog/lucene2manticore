import os, sys, time, datetime, wikiclean, re

def die(s):
	print(s)
	sys.exit(1)

source = ''
docs = 0
maxlen = 0

i = 1
while (i<len(sys.argv)):
	arg = sys.argv[i]
	if arg=='--docs':
		i += 1
		docs = int(sys.argv[i])
	elif arg=='--maxlen':
		i += 1
		maxlen = int(sys.argv[i])
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
			if maxlen>0 and len(text)>maxlen:
				nonword = text.find(' ', maxlen)
				if nonword!=-1:
					text = text[0:nonword]
			print("%d\t%s\t%d\t%s" % (docid, title, timestamp, text))
			#sys.stdout.flush()
			
		if docs!=0 and docid>=docs:
			title = ''
			break
		
		docid = docid + 1
		title = columns[0]
		timestamp = time.mktime(datetime.datetime.strptime(columns[1], "%d-%b-%Y %H:%M:%S.%f").timetuple())
		text = columns[2]

fp.close()

if len(title)>0:
	print( "%d\t%s\t%d\t%s\t" % (docid, title, timestamp, text[0:maxlen] ) )