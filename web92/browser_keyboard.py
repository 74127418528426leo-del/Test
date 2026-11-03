#!/usr/bin/env python3
"""QEMU keyboard plan for an ACTUAL Firefox address-bar HTTPS page request."""
URL="https://example.com/"
def keys_for_text(text):
    out=[]
    for c in text:
        if c.isascii() and (c.islower() and c.isalpha() or c.isdigit()):
            names=[c]
        elif c==':': names=['shift','semicolon']
        elif c=='/': names=['slash']
        elif c=='.': names=['dot']
        elif c=='-': names=['minus']
        else: raise ValueError('Unsupported keyboard symbol in public test URL')
        out.append({'keys':[{'type':'qcode','data':name} for name in names],'hold-time':75})
    return out
def sequence(url=URL):
    if not url.startswith('https://') or len(url)>159 or not url.isascii():
        raise ValueError('Test is limited to a short explicit HTTPS URL')
    ctrl_l={'keys':[{'type':'qcode','data':'ctrl'},{'type':'qcode','data':'l'}],'hold-time':100}
    enter={'keys':[{'type':'qcode','data':'ret'}],'hold-time':90}
    return [ctrl_l,*keys_for_text(url),enter]
