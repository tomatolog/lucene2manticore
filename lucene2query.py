import os, sys, re

def die(s):
	print(s)
	sys.exit(1)

source = ''
q_type = {
	'simple':['And', 'Respell', 'Term'],
	'ext2':['Or', 'Phrase', 'SloppyPhrase', 'SpanNear', 'Not'],
	'wild':['Prefix', 'Wildcard']
}
q_need = {}
q_skip = ['Fuzzy', 'IntNRQ']

dump_types = False
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
	elif arg=='--dump_types':
		dump_types = True
	elif '-' in arg:
		die ( "unknown argument %s" % arg )
	else:
		source = arg
	i += 1

if not source:
	die ( 'query source MUST be specified' )

fp = open(source, 'r')
if not fp:
	die ( 'failed to open %s', source )

groups = {}	
	
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
			
		if dump_types:
			groups[''.join([i for i in q_type_got if i.isalpha()])] = 1
		elif not any(s in q_type_got for s in q_skip) and any(s in q_type_got for s in q_need):
			
			# NOT as is
			if q_type_got.find("Not")!=-1:
				print ('%s' % q_content)
			
			# Or => term1 | termN
			elif q_type_got.find("Or")!=-1:
				print ('%s' % (" | ".join(q_content.split())))
			
			# SloppyPhrase => term1 NEAR/slope termN			
			elif q_type_got.find("SloppyPhrase")!=-1:
				q_slope_pos = q_content.find("~")
				if q_slope_pos!=-1:
					q_slope = int(q_content[q_slope_pos+1:])
					q_content = q_content[0:q_slope_pos]
					q_content = q_content.replace('"', ' ' )
					q_near = " NEAR/%d " % q_slope
					print ('%s' % (q_near.join(q_content.split())))
					
			# SpanNear => AND terms
			elif q_type_got.find("SpanNear")!=-1:
				q_slope_pos = q_content.find("//")
				if q_slope_pos!=-1:
					q_content = q_content[q_slope_pos+2:]
					print ('%s' % q_content)
					
			else:
				q_content = q_content.replace('//', ' ' )
				print ('%s' % q_content)

if dump_types:
	for key in sorted(groups.iterkeys()): print "%s" % (key)
		
fp.close()
