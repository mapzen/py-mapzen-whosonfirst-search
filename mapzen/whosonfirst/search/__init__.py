import types
import os
import os.path
import csv
import json
import geojson
import logging
import math
import tempfile

import urllib
import requests

import mapzen.whosonfirst.machinetag
import machinetag.elasticsearch.hierarchy

import mapzen.whosonfirst.utils
import mapzen.whosonfirst.placetypes
import mapzen.whosonfirst.elasticsearch
import mapzen.whosonfirst.uri

class index(mapzen.whosonfirst.elasticsearch.index):

    def __init__(self, **kwargs):

        mapzen.whosonfirst.elasticsearch.index.__init__(self, **kwargs)

    def prepare_feature(self, feature):

        props = feature['properties']

        id = props['wof:id']

        doctype = props['wof:placetype']
        body = self.prepare_geojson(feature)

        return {
            'id': id,
            'index': self.index,
            'doc_type': doctype,
            'body': body
        }

    # https://stackoverflow.com/questions/20288770/how-to-use-bulk-api-to-store-the-keywords-in-es-by-using-python

    def prepare_feature_bulk(self, feature):
    
        props = feature['properties']
        id = props['wof:id']

        doctype = props['wof:placetype']

        body = self.prepare_geojson(feature)

        return {
            '_id': id,
            '_index': self.index,
            '_type': doctype,
            '_source': body
        }

    def prepare_geojson(self, geojson):

        props = geojson['properties']

        # Store a stringified bounding box so that tools like
        # the spelunker can zoom to extent and stuff like that
        # (20150730/thisisaaronland)

        bbox = geojson.get('bbox', [])

        # https://github.com/whosonfirst/py-mapzen-whosonfirst-search/issues/25

        if len(bbox) == 4:

            minlon, minlat, maxlon, maxlat = bbox

            props['geom:min_latitude'] = minlat
            props['geom:min_longitude'] = minlon
            props['geom:max_latitude'] = maxlat
            props['geom:max_longitude'] = maxlon

        bbox = map(str, bbox)	# oh python...
        bbox = ",".join(bbox)

        props['geom:bbox'] = bbox

        # ggggggrgrgrgrgrhhnhnnnhnhnhnhnhhzzzzpphphtttt - we shouldn't
        # have to do this but even with the enstringification below
        # ES tries to be too clever by half so in the interests of just
        # getting stuff done we're going to be ruthless about things...
        # (21050806/thisisaaronland)

        omgwtf = (
            u'ne:fips_10_',
            u'ne:gdp_md_est',
            u'ne:geou_dif',
            u'ne:pop_est',
            u'ne:su_dif',
            u'ne:FIPS_10_',
            u'ne:ISO_A3_EH',
            u'ne:adm0_dif',
            u'ne:level',
            u'fsgov:ajo_pvm',
            u'statoids:as_of_date',
        )

        for bbq in omgwtf:
            if props.has_key(bbq):
                logging.debug("remove tag '%s' because ES suffers from E_EXCESSIVE_CLEVERNESS" % bbq)
                del(props[bbq])

        # alt placetype names/ID

        placetype = props['wof:placetype']

        try:
            placetype = mapzen.whosonfirst.placetypes.placetype(placetype)

            placetype_id = placetype.id()
            placetype_names = []
            
            for n in placetype.names():
                placetype_names.append(unicode(n))

            props['wof:placetype_id'] = placetype_id
            props['wof:placetype_names'] = placetype_names
            
        except Exception, e:
            logging.warning("Invalid or unknown placetype (%s) - %s" % (placetype, e))

        # Dates

        # there used to be code here to set "private" ES date fields for EDTF stuff
        # but it has been removed in favour of explicit date:inception/cessation_upper/lower
        # properties that get added by py-mapzen-whosonfirst-export 0.9.9 +
        # (20180504/thisisaaronland)
              
        # Categories

        categories = []

        # wof categories

        wof_categories = []

        for tag in props.get('wof:categories', []):

            mt = mapzen.whosonfirst.machinetag.machinetag(tag)

            if not mt.is_machinetag():
                logging.warning("%s is not a valid wof:categories machine tag, skipping" % tag)
                continue

            enpathified = machinetag.elasticsearch.hierarchy.enpathify_from_machinetag(mt)

            if not enpathified in wof_categories:
                wof_categories.append(enpathified)

        props["wof:categories"] = wof_categories

        # mz categories

        mz_categories = []

        for tag in props.get('mz:categories', []):

            mt = mapzen.whosonfirst.machinetag.machinetag(tag)

            if not mt.is_machinetag():
                logging.warning("%s is not a valid wof:categories machine tag, skipping" % tag)
                continue

            enpathified = machinetag.elasticsearch.hierarchy.enpathify_from_machinetag(mt)

            if not enpathified in mz_categories:
                mz_categories.append(enpathified)

        props["mz:categories"] = mz_categories

        # simplegeo categories

        sg_categories = []
        
        for tag in props.get('sg:categories', []):

            mt = mapzen.whosonfirst.machinetag.machinetag(tag)

            if not mt.is_machinetag():
                logging.warning("%s is not a valid sg:categories machine tag, skipping" % tag)
                continue

            enpathified = machinetag.elasticsearch.hierarchy.enpathify_from_machinetag(mt)

            if not enpathified in sg_categories:
                sg_categories.append(enpathified)

        # old historical stuff that we may ignore/purge in time... but
        # not today (20160613/thisisaaronland)

        stz = mapzen.whosonfirst.machinetag.sanitize()

        for cl in props.get('sg:classifiers', []):

            sg_type = cl.get('type', '')
            sg_category = cl.get('category', '')
            sg_subcategory = cl.get('subcategory', '')

            clean_type = stz.filter_namespace(sg_type)
            clean_category = stz.filter_predicate(sg_category)
            clean_subcategory = stz.filter_value(sg_subcategory)

            tags = []

            mt = "sg:%s=%s" % (clean_type, clean_category)
            tags.append(mt)

            if clean_subcategory != "":
                mt = "%s:%s=%s" % (clean_type, clean_category, clean_subcategory)
                tags.append(mt)

            for t in tags:

                mt = mapzen.whosonfirst.machinetag.machinetag(t)

                if not mt.is_machinetag():
                    logging.warning("sg category fails machinetag test: '%s' (%s)" % (t, cl))
                    continue

                enpathified = machinetag.elasticsearch.hierarchy.enpathify_from_machinetag(mt)

                if not enpathified in sg_categories:
                    sg_categories.append(enpathified)

        props["sg:categories"] = sg_categories

        # Concordances

        conc = props.get('wof:concordances', {})


        # Because Boundary Issues was careless with how it encoded 'array()'
        # See: https://github.com/whosonfirst/whosonfirst-www-boundaryissues/commit/436607e41b51890080064515582240bbedda633f
        # (20161031/dphiffer)
        if conc == []:
            logging.warning("FIX %d concordances encoded as []" % props['wof:id'])
            conc = {}

        # So this may go away if we can ever figure out a simple way to facet on the
        # set of unique keys for _all_ `wof:concordances` blobs but today we can't so
        # this is faster and easier than standing around in ES-quicksand...
        # (20160518/thisisaaronland)

        props['wof:concordances_sources'] = conc.keys()

        # Misc counters

        # https://github.com/whosonfirst/py-mapzen-whosonfirst-search/issues/13

        props['counts:concordances_total'] = len(conc.items())

        # https://github.com/whosonfirst/py-mapzen-whosonfirst-search/issues/14

        langs_official = props.get('wof:lang_x_official', [])
        langs_spoken = props.get('wof:lang_x_spoken', [])

        props['counts:languages_official'] = len(langs_official)
        props['counts:languages_spoken'] = len(langs_spoken)

        count_langs = len(langs_official)

        for lang in langs_spoken:

            if not lang in langs_official:
                count_langs += 1

        props['counts:languages_total'] = count_langs

        # https://github.com/whosonfirst/py-mapzen-whosonfirst-search/issues/15

        count_names_total = 0
        count_names_prefered = 0
        count_names_variant = 0
        count_names_colloquial = 0
        count_names_languages = 0

        name_langs = []

        translations = [];

        for k, v in props.items():

            if not k.startswith("name:"):
                continue

            count_names = len(v)
            count_names_total += count_names

            # https://github.com/whosonfirst/whosonfirst-names/issues/3

            try:
                k = k.replace("name:", "")
                parts = k.split("_x_")

                lang, qualifier = parts

                # eng

                if not lang in translations:
                    translations.append(lang)

                # eng_x_prefered

                if not k in translations:
                    translations.append(k)

            except Exception, e:
                logging.warning("failed to parse '%s', because %s" % (k, e))
                continue

            if not lang in name_langs:
                count_names_languages += 1
                name_langs.append(lang)

            if qualifier == 'prefered':
                count_names_prefered += count_names
            elif qualifier == 'variant':
                count_names_variant += count_names
            elif qualifier == 'colloquial':
                count_names_colloquial += count_names
            else:
                pass

        props['translations'] = translations

        props['counts:names_total'] = count_names_total
        props['counts:names_prefered'] = count_names_prefered
        props['counts:names_variant'] = count_names_variant
        props['counts:names_colloquial'] = count_names_colloquial
        props['counts:names_languages'] = len(name_langs)

        # https://github.com/whosonfirst/py-mapzen-whosonfirst-search/issues/3

        try:
            props['geom:type'] = geojson['geometry']['type']
        except Exception, e:

            wofid = props["wof:id"]
            logging.error("Hey wait a minute... %s is missing a geometry.type property" % wofid)

            raise Exception, e

        # because ES suffers from E_EXCESSIVE_CLEVERNESS

        # Because, for a time, Boundary Issues did not have the capacity to
        # *remove* properties, and I was incorrectly setting edtf:deprecated
        # to 'uuuu'. (20161103/dphiffer)

        if "edtf:deprecated" in props and props['edtf:deprecated'] in ("uuuu", ""):
            logging.debug("FIX %d edtf:deprecated set to uuuu" % props['wof:id'])
            del props['edtf:deprecated']

        #
        
        fh = tempfile.NamedTemporaryFile()
        tmpname = fh.name

        json.dump(geojson, fh)
        fsize = os.stat(tmpname).st_size

        fh.close()

        # this should never happen because fh.close should
        # remove the file but just in case...
        
        if os.path.exists(tmpname):
            os.unlink(tmpname)

        props['mz:filesize'] = fsize
        
        #
 
        props = self.enstringify(props)
        return props

    def enstringify(self, data, **kwargs):

        ima_int = (
            'continent_id',
            'country_id',
            'county_id',
            'gn:elevation',
            'gn:population',
            'gn:id',
            'gp:id',
            'locality_id',
            'neighbourhood_id',
            'region_id',
            'wof:id',
            'wof:belongsto',
            'wof:breaches',
            'wof:lastmodified',
            'wof:megacity',
            'wof:placetype_id',
            'wof:population',
            'wof:scale',
            'wof:superseded_by',
            'wof:supersedes',
            'zs:pop10',
        )

        ima_float = (
            'geom:area',
            'geom:latitude',
            'geom:longitude',
            'lbl:latitude',
            'lbl:longitude',
            'mps:latitude',
            'mps:longitude',
            'mz:min_zoom',
            'mz:max_zoom',
        )

        ima_int_wildcard = (
        )

        ima_float_wildcard = (
            'ne:',
        )

        isa = type(data)

        if isa == types.DictType:

            for k, v in data.items():
                k = unicode(k)
                v = self.enstringify(v, key=k)
                data[k] = v

            return data

        elif isa == types.ListType:

            str_data = []

            for thing in data:
                str_data.append(self.enstringify(thing, **kwargs))

            return str_data

        elif isa == types.NoneType:
            return unicode("")

        else:

            k = kwargs.get('key', None)
            logging.debug("processing %s: %s" % (k,data))

            if k and k in ima_int:

                if data == '':
                    return 0

                # I seriously hate you, Python...
                # int('579.0')
                # Traceback (most recent call last):
                #   File "<stdin>", line 1, in <module>
                # int(float('589.0'))
                # 589
                #
                # (20181029/thisisaaronland)
                
                return int(float(data))

            elif k and k in ima_float:

                if data == '':
                    return 0.0

                return float(data)

            else:

                if k:

                    for fl_k in ima_int_wildcard:
                        if k.startswith(fl_k):

                            try:
                                data = int(data)
                                return data
                            except Exception, e:
                                logging.debug("failed to convert %s to an int because %s" % (k.encode('utf8'), e))

                    for fl_k in ima_float_wildcard:
                        if k.startswith(fl_k):

                            try:
                                data = float(data)
                                return data
                            except Exception, e:
                                logging.debug("failed to convert %s to a float because %s" % (k.encode('utf8'), e))

                return unicode(data)

    def load_file(self, f):

        try:
            fh = open(f, 'r')
            return geojson.load(fh)
        except Exception, e:
            logging.error("failed to open %s, because %s" % (f, e))
            raise Exception, e

    def prepare_file(self, f):

        data = self.load_file(f)
        data = self.prepare_feature(data)
        return data

    def prepare_file_bulk(self, f):

        logging.debug("prepare file %s" % f)

        data = self.load_file(f)

        try:
            data = self.prepare_feature_bulk(data)
            logging.debug("yield %s" % data)
        except Exception, e:
            logging.warning("failed to prepare data for %s because %s" % (f, e))
            raise Exception, e

        return data

    def prepare_files_bulk(self, files):

        for path in files:

            logging.debug("prepare file %s" % path)

            if mapzen.whosonfirst.uri.is_alt_file(path):
                logging.warning("%s is an alt file so not indexing it" % path)
                continue

            data = self.prepare_file_bulk(path)
            logging.debug("yield %s" % data)

            yield data

    def index_feature(self, feature):

        prepped = self.prepare_feature(feature)
        return self.index_document(prepped)

    def index_file(self, path):

        if mapzen.whosonfirst.uri.is_alt_file(path):
            logging.warning("%s is an alt file so not indexing it" % path)
            return False

        path = os.path.abspath(path)
        data = self.prepare_file(path)

        return self.index_document(data)

    def index_files(self, files):

        iter = self.prepare_files_bulk(files)

        return self.index_documents_bulk(iter)

    def index_filelist(self, path, **kwargs):

        def mk_files(fh):
            for ln in fh.readlines():
                path = ln.strip()

                if kwargs.get('prefix', None):
                    path = os.path.join(kwargs['prefix'], path)

                if mapzen.whosonfirst.uri.is_alt_file(path):
                    logging.warning("%s is an alt file so not indexing it" % path)
                    continue

                logging.debug("index %s" % path)
                yield path

        fh = open(path, 'r')
        files = mk_files(fh)

        iter = self.prepare_files_bulk(files)

        return self.index_documents_bulk(iter)

    def delete_feature(self, feature):

        props = feature['properties']
        id = props['wof:id']

        doctype = props['wof:placetype']

        kwargs = {
            'id': id,
            'index': self.index,
            'doc_type': doctype,
            'refresh': True
        }

        self.delete_document(kwargs)

class search(mapzen.whosonfirst.elasticsearch.search):

    def __init__(self, **kwargs):

        mapzen.whosonfirst.elasticsearch.query.__init__(self, **kwargs)

    def enfeaturify(self, row):

        properties = row['_source']
        id = properties['wof:id']

        geom = {}
        bbox = []

        lat = None
        lon = None

        if not properties.get('wof:path', False):

            path = mapzen.whosonfirst.utils.id2relpath(id)
            properties['wof:path'] = path

        if properties.get('geom:bbox', False):
            bbox = properties['geom:bbox']
            bbox = bbox.split(",")

        if properties.get('geom:latitude', False) and properties.get('geom:longitude', False):
            lat = properties['geom:latitude']
            lat = properties['geom:longitude']

        elif len(bbox) == 4:
            pass	# derive centroid here...

        else:
            pass

        if properties.get('wof:placetype', None) == 'venue' and lat and lon:
                geom = {'type': 'Point', 'coordinates': [ lon, lat ] }

        return {
            'type': 'Feature',
            'id': id,
            'bbox': bbox,
            'geometry': geom,
            'properties': properties
        }

class query(search):

    def __init__(self, **kwargs):

        logging.warning("mapzen.whosonfirst.search.query is deprecated - please use mapzen.whosonfirst.search.search")
        search.__init__(self, **kwargs)

if __name__ == '__main__':

    print "Please rewrite me"
