import os
import urllib

def is_ws(c):
    return c == ' ' or c == '\t'

def eat_ws(l, n, pos):
    while pos < n and is_ws(l[pos]):
        pos += 1
    return pos

def match_string(l, n, pos, end_brace = False):
    pos = eat_ws(l, n, pos)
    if pos == n:
        return None, n

    if l[pos] == '"':
        pos += 1
        start = pos
        while pos < n and l[pos] != '"':
            pos += 1
        if pos == n:
            return None, n
        s = l[start:pos]
        return s, pos+1
    else:
        start = pos
        while pos < n and not is_ws(l[pos]) and (not end_brace or l[pos] != '}'):
            pos += 1
        s = l[start:pos]
        return s, pos

def match_doc(doc_text):
    doc = {}
    doc['nodes'] = []
    ts = {'b':False, 'i':False, 'u':False}
    node = None

    lines = doc_text.split('\n')
    for l in lines:
        n = len(l)
        if node is None:
            if n >= 1 and l[0] == '@':
                pos = 1
                arr = []
                while pos < n:
                    s, pos = match_string(l, n, pos)
                    if s is not None:
                        arr.append(s)
                if len(arr) >= 1:
                    cmd = arr[0].lower()
                    if cmd == 'node':
                        if len(arr) >= 2:
                            in_node = True
                            node = {}
                            node['name'] = arr[1]
                            node['text'] = []
                            doc['nodes'].append(node)

                            if len(arr) >= 3:
                                node['title'] = [arr[2]]
                    else:
                        doc[cmd] = arr[1:]
        else:
            if n >= 1 and l[0] == '@' and (n == 1 or l[1] != '{'):
                pos = 1
                arr = []
                while pos < n:
                    s, pos = match_string(l, n, pos)
                    if s is not None:
                        arr.append(s)
                if len(arr) >= 1:
                    cmd = arr[0].lower()
                    if cmd == 'endnode':
                        node = None
                        for k in ts:
                            ts[k] = False
                    else:
                        node[cmd] = arr[1:]
            else:
                pos = 0
                while pos < n:
                    span = ''
                    while pos < n and not (l[pos] == '@' and pos+1 < n and l[pos+1] == '{'):
                        ESC = {'\\':'\\', '@':'@'}
                        if l[pos] == '\\' and pos+1 < n and l[pos+1] in ESC:
                            span += ESC[l[pos+1]]
                            pos += 2
                        else:
                            span += l[pos]
                            pos += 1

                    if len(span) != 0:
                        node['text'].append(('span', span, [k for k, v in ts.items() if v]))

                    if pos < n:
                        pos += 2
                        is_attr_cmd = pos < n and l[pos] == '"'

                        arr = []
                        while pos < n and l[pos] != '}':
                            s, pos = match_string(l, n, pos, True)
                            if s is not None:
                                arr.append(s)

                        if pos < n:
                            pos += 1
                            if is_attr_cmd and len(arr) >= 2:
                                attr_cmd = arr[1].lower()
                                if len(arr) >= 3 and attr_cmd == 'link':
                                    node['text'].append(('link', arr[0], arr[2]))
                            elif not is_attr_cmd and len(arr) >= 1:
                                attr = arr[0].lower()
                                if len(arr) == 1:
                                    if attr in ['b', 'i', 'u']:
                                        ts[attr] = True
                                    elif attr in ['ub', 'ui', 'uu']:
                                        ts[attr[1:]] = False
                                    elif attr == 'plain':
                                        for k in ts:
                                            ts[k] = False

                node['text'].append(('br',))

    return doc

def node_link(nn):
    i = nn.find('/')
    if i != -1:
        fn = fix_filename(nn[:i])
        return fn + '#' + urllib.quote_plus(nn[i+1:].lower())
    else:
        return '#' + urllib.quote_plus(nn.lower())

def doc_to_html(doc):
    title = (doc.get('database', []) + ['Unknown database'])[0]

    output = '<html>\n<head>\n'
    output += '<title>' + title + '</title>\n'
    output += '</head>\n<body>\n'

    for node in doc['nodes']:
        output += '<div id="' + urllib.quote_plus(node['name'].lower()) + '">\n<hr/>\n'

        if 'title' in node and len(node['title']) == 1:
            output += '<p><b>' + node['title'][0] + '</b></p>\n'

        output += '<p>'
        for tag, text in [('toc', 'Contents'), ('index', 'Index'), ('help', 'Help'), ('prev', 'Prev'), ('next', 'Next')]:
            if tag in node and len(node[tag]) == 1:
                output += '<a href="' + node_link(node[tag][0]) + '">' + text + '</a> '
            else:
                output += '<a>' + text + '</a> '
        output += '</p>\n'

        output += '<pre>\n'
        for tag in node['text']:
            if tag[0] == 'br':
                output += '\n'
            elif tag[0] == 'span':
                _, text, ts = tag
                for e in ts:
                    output += '<' + e + '>'
                output += text.replace('<', '&lt;')
                for e in ts:
                    output += '</' + e + '>'
            elif tag[0] == 'link':
                _, label, node_name = tag
                output += '<a href="' + node_link(node_name) + '">' + label + '</a>'
        output += '</pre>\n</div>\n'

    output += '<hr/>\n</body>\n</html>\n'
    return output

def fix_filename(fn):
    if fn.lower().endswith('.guide'):
        fn = fn[:-6]
    return fn + '.html'

def convert(fn):
    with open(fn) as f:
        doc = match_doc(f.read())
    with open(fix_filename(fn), 'w') as f:
        f.write(doc_to_html(doc))

if __name__ == '__main__':
    for fn in os.listdir('.'):
        if fn.lower().endswith('.guide'):
            convert(fn)
