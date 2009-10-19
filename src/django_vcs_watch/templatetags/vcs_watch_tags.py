import datetime
import pytz

from pdb import set_trace
from django import template
from django_vcs_watch.models import Commit, Repository, Feed, FeedItem
from django_vcs_watch.utils import get_user_feed_slug

register = template.Library()

@register.inclusion_tag('django_vcs_watch/top_repositories.html')
def top_repositories():
    results = Commit.objects \
        .group(
            keys = ['slug'],
            condition = {
                'date': {'$gte' : datetime.datetime.utcnow() - datetime.timedelta(7)}
            },
            initial = {'count': 0},
            reduce = 'function(obj, prev) { prev.count++; }'
        )
    results = sorted(results, key=lambda x: x['count'], reverse = True)[:10]
    results = Repository.objects \
        .find({'slug': {'$in': [r['slug'] for r in results]}})

    return {
        'objects': results
    }



def parse_token(token):
    tokens = token.split_contents()[1:]
    result = {}
    for token in tokens:
        name, value = token.split(':')
        if value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        else:
            value = template.Variable(value)
        result[name] = value
    return result



def resolve_variables(vars, context):
    result = vars.copy()
    for name, value in result.iteritems():
        resolve = getattr(value, 'resolve', None)
        if resolve is not None:
            result[name] = resolve(context)
    return result



class GetObjectList(template.Node):
    def __init__(self,
                 cls,
                 vars = {},
                 query = {},
                 on_page = 20,
                 map_func = lambda x: x,
                ):
        self.cls = cls
        self.vars = vars
        self.query = query
        self.on_page = int(vars.get('on_page', on_page))
        self.map_func = map_func


    def render(self, context):
        context['request'].GET.get('tb', None)

        vars = resolve_variables(self.vars, context)

        if callable(self.query):
            self.query = self.query(context, vars)

        cursor = self.cls.objects.find(self.query)

        context[self.vars.get('as', 'object_list')] = map(self.map_func, cursor[:self.on_page])
        return ''



class GetObject(template.Node):
    def __init__(self,
                 cls,
                 vars = {},
                 query = {},
                ):
        self.cls = cls
        self.vars = vars
        self.query = query


    def render(self, context):
        vars = resolve_variables(self.vars, context)

        if callable(self.query):
            self.query = self.query(context, vars)

        object = self.cls.objects.find_one(self.query)
        context[self.vars.get('as', 'object')] = object
        return ''



def get_tb(context):
    request = context['request']
    if 'tb' in request.GET:
        return pytz.utc.localize(
            datetime.datetime.utcfromtimestamp(
                int(request.GET.get('tb'))))
    return pytz.utc.localize(datetime.datetime.utcnow())



@register.tag
def get_all_commits(parser, token):
    vars = parse_token(token)
    return GetObjectList(
        cls = Commit,
        vars = vars,
        query = lambda context, vars: {
            'date' : {'$lt': get_tb(context)}
        },
    )


@register.tag
def get_commits_with_slug(parser, token):
    vars = parse_token(token)
    return GetObjectList(
        cls = Commit,
        vars = vars,
        query = lambda context, vars: dict(
            slug = vars['slug'],
            date = {'$lt': get_tb(context)}
        ),
    )

@register.tag
def get_commits_from_user_feed(parser, token):
    vars = parse_token(token)

    def process_commit(feed_item):
        commit = feed_item.commit
        commit.from_filtered_feed = True
        return commit

    return GetObjectList(
        cls = FeedItem,
        vars = vars,
        query = lambda context, vars: dict(
            slug = get_user_feed_slug(context['request'].user),
            date = {'$lt': get_tb(context)}
        ),
        map_func = process_commit,
    )

@register.tag
def get_commits_by(parser, token):
    vars = parse_token(token)
    return GetObjectList(
        cls = Commit,
        vars = vars,
        query = lambda context, vars: dict(
            author = vars['author'],
            date = {'$lt': get_tb(context)}
        ),
    )


@register.tag
def get_user_feed(parser, token):
    vars = parse_token(token)
    return GetObject(
        cls = Feed,
        vars = vars,
        query = lambda context, vars: dict(
            _id = get_user_feed_slug(context['request'].user),
        ),
    )

