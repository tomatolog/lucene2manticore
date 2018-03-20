import os, sys, json
from icecream import ic

def die(s):
	print(s)
	sys.exit(1)

def ic_print(s):
	print(s)

ic.configureOutput(outputFunction=ic_print)
	
if not sys.argv[1:]:
	print ("""Usage: dict2stopwords.py [OPTIONS] dictionary_dump
Options are:
--top\t\tuse N top frequent terms from dump of dictionary (default 1000)
--dumptop\tdump top terms along with frequencies
--json\t\toutput should be JSON array of strings
""")
	sys.exit ( 0 )
	
dict = None
topN = 1000
dump_top = False
json_output = False

i = 1
while (i<len(sys.argv)):
	arg = sys.argv[i]
	if arg=='--top':
		i += 1
		topN = int(sys.argv[i])
	elif arg=='--dumptop':
		dump_top = True
	elif arg=='--json':
		json_output = True
	elif '--' in arg:
		die ( "unknown argument %s" % arg )
	else:
		dict = arg
	i += 1

if not dict:
	die ( 'dictionary source MUST be specified' )

terms = []

fp = open(dict, 'r')
if not fp:
	die ( 'failed to open %s', dict )

for line in iter(fp.readline, ''):
	# keyword,docs,hits,offset
	t = line.split(',')
	terms.append ((t[0], int(t[1])))
fp.close()

top_terms = sorted(terms, key=lambda t: t[1], reverse=True)
top_terms = top_terms[0:topN]

if dump_top:
	for t in top_terms:
		print ( "%s, %d" % (t[0], t[1]) )
else:
	top_terms = sorted(top_terms)
	if json_output:
		top_terms_json = [t[0] for t in top_terms]
		print(json.dumps(top_terms_json, ensure_ascii=False))
	else:
		for t in top_terms:
			print ( t[0] )
