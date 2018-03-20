import logging
import os, json, traceback
from esrally.utils import console

from icecream import ic

logger = logging.getLogger("rally.utils.io")

def refresh(es, params):
    es.indices.refresh(index=params.get("index", "_all"))

class TermList:
    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
            if len(track.indices[0].types) == 1:
                default_type = track.indices[0].types[0].name
            else:
                default_type = None
        else:
            default_index = "_all"
            default_type = None

        self._index_name = params.get("index", default_index)
        self._type_name = params.get("type", default_type)
        self.queries = []
        if "queries" in params:
            self.queries = params["queries"]
        self.no_score = False
        if "no_score" in params:
            self.no_score = params["no_score"]

        self.cur_q = 0
        self.total_q = len(self.queries)
        if self.total_q==0:
            self.queries = ["test"]
            self.total_q = 1
            console.warn("no queries found", logger=logger)

    def partition(self, partition_index, total_partitions):
        return self

    def size(self):
        return 1

    def params(self):
        # you must provide all parameters that the runner expects
        q = self.queries[self.cur_q]
        self.cur_q = (self.cur_q + 1) % self.total_q
        req = {
            "body": { "query": q },
            "index": self._index_name,
            "use_request_cache": False
        }
        if self.no_score:
            req["body"]["sort"] = [self.no_score]
            req["body"]["track_scores"] = False
        return req


def register(registry):
    try:
        major, minor, patch, _ = registry.meta_data["rally_version"]
        registry.register_param_source("term-list-params", TermList)
        
    except AttributeError:
        # We must be below Rally 0.8.2 (did not provide version metadata).
        # register "refresh" for older versions of Rally. Newer versions have support out of the box.
        registry.register_runner("refresh", refresh)
