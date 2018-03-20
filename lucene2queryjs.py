import os, sys, re, json
from icecream import ic

def die(s):
	print(s)
	sys.exit(1)

def ic_print(s):
	print(s)

ic.configureOutput(outputFunction=ic_print)
	
if not sys.argv[1:]:
	print ("""Usage: lucene2queryjs.py [OPTIONS] queries
Options are:
--types\t\tprocess only this type of queries simple,ext2,wild (default simple)
--name\t\tname for rally operation (default term-file)
--field\t\tfield of match operator
--low_terms\tprocess only terms with low frequency mark
""")
	sys.exit ( 0 )
	
sources = []
q_type = {
	'simple':['And', 'Respell', 'Term'],
	'ext2':['Or', 'Phrase', 'SloppyPhrase', 'SpanNear', 'Not'],
	'wild':['Prefix', 'Wildcard']
}
q_need = q_type['simple']
q_skip = ['Fuzzy', 'IntNRQ', 'TermBGroup', 'TermGroup', 'TermDayOf', 'TermMonth']
op_name = 'term-file'
field = "body"
low_terms = False

i = 1
while (i<len(sys.argv)):
	arg = sys.argv[i]
	if arg=='--types':
		i += 1
		need = sys.argv[i]
		if need not in q_type:
			print ( "unknown query type %s" % need )
		else:
			q_need = q_type[need]
	elif arg=='--name':
		i += 1
		op_name = sys.argv[i]
	elif arg=='--field':
		i += 1
		field = sys.argv[i]
	elif arg=='--low_terms':
		low_terms = True
	elif '-' in arg:
		die ( "unknown argument %s" % arg )
	else:
		sources.append(arg)
	i += 1

if len(sources)==0:
	die ( 'query source MUST be specified' )

queries = []

for source in sources:	
	fp = open(source, 'r')
	if not fp:
		die ( 'failed to open %s', source )

	for query in iter(fp.readline, ''):
		q = query.rstrip('\n')
		q_type_pos = q.find(':')
		if q_type_pos!=-1:
			q_type_got = q[0:q_type_pos]
			q_content = q[q_type_pos+1:]
			
			q_tail_pos = q_content.find('#')
			if q_tail_pos!=-1:
				q_content = q_content[0:q_tail_pos]
				
			q_facet_pos = q_content.find('+facets:')
			if q_facet_pos!=-1:
				q_content = q_content[0:q_facet_pos]
				
			q_filter_pos = q_content.find('+filter=')
			if q_filter_pos!=-1:
				q_content = q_content[0:q_filter_pos]

			# to make parsing similar
			# got rid of utf8 encoded chars 
			if q_content!=q_content.decode('utf-8','ignore').encode('latin-1','ignore'):
				continue
			# got rid of query with numbers but not at SloppyPhrase
			if len([c for c in q_content if c.isdigit()])>0 and q_type_got.find("SloppyPhrase")==-1:
				continue
				
			if low_terms and ( "Low" not in q_type_got or "High" in q_type_got ):
				continue
			
			if not any(s in q_type_got for s in q_skip) and any(s in q_type_got for s in q_need):
				
				# NOT => and terms + not terms
				if q_type_got.find("Not")!=-1:
					q_terms = q_content.split()
					q_must = []
					q_must_not = []
					for term in q_terms:
						if term[0]=='-':
							q_must_not.append({"match": {field: term[1:]}})
						else:
							q_must.append({"match": {field: term}})
					queries.append({"bool":{"must":q_must, "must_not":q_must_not}})
					continue
				
				# Or => term1 | termN
				elif q_type_got.find("Or")!=-1:
					terms = [ {"match": {field: term}} for term in q_content.split()]
					queries.append({"bool":{"should":terms}})
					continue
				
				# SloppyPhrase => term1 NEAR/slope termN			
				elif q_type_got.find("SloppyPhrase")!=-1:
					q_slope_pos = q_content.find("~")
					if q_slope_pos!=-1:
						q_slope = int(q_content[q_slope_pos+1:])
						q_content = q_content[0:q_slope_pos]
						q_content = q_content.replace('"', ' ' ).strip()
						queries.append({'match_phrase': {field: {"query":q_content, "slop":q_slope}}})
					continue
						
				# SpanNear => AND terms
				elif q_type_got.find("SpanNear")!=-1:
					q_slope_pos = q_content.find("//")
					if q_slope_pos!=-1:
						q_content = q_content[q_slope_pos+2:]
						terms = [ {"match": {field: term}} for term in q_content.split()]
						queries.append({"bool":{"must":terms}})
					continue

				# Phrase => Phrase terms
				elif q_type_got.find("Phrase")!=-1:
					terms = q_content.replace('"', ' ' ).strip()
					queries.append({'match_phrase': {field: terms}})
					continue
					
				else:
					q_content = q_content.translate(None, '//+,.:\'')
					queries.append({"match": {field: {"query":q_content, "operator" : "and"}}})
			
	fp.close()

#ic(queries)

print """
{
	"name": "%s",
	"operation-type": "search",
	"param-source": "term-list-params",
	"queries": [""" % op_name

i = 0
queries_count = len(queries)
while i<queries_count:
	q = queries[i]
	print("\t\t%s%s" % (json.dumps(q, ensure_ascii=False), ',' if i+1<queries_count else ''))
	i = i+1

#print (json.dumps(queries))
	
print """	]
}    
"""