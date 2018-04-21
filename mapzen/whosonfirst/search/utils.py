# should this really be in this package since this package is spelunker-specific and
# these are meant to be common methods for not-necessarily-spelunker-ish things - I 
# don't know and probably not but it will do for now (20180420/thisisaaronland)

import edtf
import arrow
import logging

def append_edtf_date_ranges(props, inception, cessation):

    append = False

    fmt = "YYYY-MM-DD"

    # skip "uuuu" because it resolves to 0001-01-01 9999-12-31
        
    if not inception in ("", "uuuu"):
        try:
            
            e = edtf.parse_edtf(unicode(inception))

            lower = arrow.get(e.lower_strict())
            upper = arrow.get(e.upper_strict())

            props["date_inception_lower"] = lower.format(fmt)
            props["date_inception_upper"] = upper.format(fmt)

            append = True

        except Exception, e:
            logging.warning("Failed to parse inception '%s' because %s" % (inception, e))

    if not cessation in ("", "uuuu", "open"):                

        # we'll never get here because of the test above but the point
        # is a) edtf.py freaks out when an edtf string is just "open" (not
        # sure if this is a me-thing or a them-thing and b) edtf.py interprets
        # "open" as "today" which is not what we want to store in the database
        # (20180418/thisisaaronland)
        
        if cessation == "open" and not inception in ("", "uuuu"):
            cessation = "%s/open" % inception
                
        try:                
            e = edtf.parse_edtf(unicode(cessation))

            lower = arrow.get(e.lower_strict())
            upper = arrow.get(e.upper_strict())

            props["date_cessation_lower"] = lower.format(fmt)
            props["date_cessation_upper"] = upper.format(fmt)
            
            append = True

        except Exception, e:
            logging.warning("Failed to parse cessation '%s' because %s" % (cessation, e))
                            
    return append
    
