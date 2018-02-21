# lucene2manticore

Converters for Manticoresearch from Lucene perfomance utils.

lucene2tsv converts source data from Lucene TSV like file to proper TSV file.

lucene2query converts Lucene tasks to Manticoresearch queries.

```
Usage: python lucene2tsv.py data/lucene.tsv --maxlen 2097152 > data/manticore.tsv
--maxlen max document size (0 by default, convert whole document)
--docs process only N first documents (0 by default, convert all docuemnts)
```

```
Usage: python lucene2query.py --types simple data/wikimedium500.tasks > query/q-wiki500-simple.txt
--types convert only specified type of query (by default convert all types of queries)
--dump_types output all types of query found at task file
```
