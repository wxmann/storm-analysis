from html.parser import HTMLParser


def get_image_srcs(html, filter_results=None):
    parser = ImagesHTMLParser()
    parser.feed(html)
    return parser.results(filter_results)


class ImagesHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.foundimages = []

    def handle_starttag(self, tag, attrs):
        self.foundimages += [attrval for attr, attrval in attrs if tag.lower() == 'img' and attr.lower() == 'src']

    def results(self, filter_results=None):
        if filter_results is None:
            return self.foundimages
        else:
            return [img for img in self.foundimages if filter_results(img)]