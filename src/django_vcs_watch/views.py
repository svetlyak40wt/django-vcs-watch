import re
import pymongo

from collections import defaultdict
from pdb import set_trace

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic.create_update import apply_extra_context, redirect

from django_vcs_watch.models import Repository, Commit, Feed
from django_vcs_watch.forms import RepositoryForm
from django_vcs_watch.utils import get_user_feed_slug

_WRAPPERS = defaultdict(lambda: lambda x:x, {
    'repositories': Repository,
    'commits': Commit,
})


@login_required
def profile(request):
    from django.views.generic.list_detail import object_list
    return object_list(
            request,
            queryset=request.user.repository_set.all())


def autocomplete(request, **kwargs):
    q = request.GET.get('q', '')
    #db.repositories.ensure_index([('url', pymongo.ASCENDING)])

    return object_list(
            request,
            cls = Repository,
            query = {'url': re.compile(q)},
            **kwargs)

# TODO move this to separate django app like django-annoing
from django.contrib.syndication.views import feed as contrib_feed


def feed(request, slug, param = '', feed_dict = None):
    url = slug
    if param:
        url += '/' + param
    return contrib_feed(request, url, feed_dict = feed_dict)


def create(request,
           template_name,
           form_class = RepositoryForm,
           post_save_redirect = None,
           extra_context = {},
           template_loader = loader,
           context_processors = None,
          ):
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            new_object = form.save()
            return redirect(post_save_redirect, new_object)
    else:
        form = form_class()

    t = template_loader.get_template(template_name)
    c = RequestContext(request, {
        'form': form,
    }, context_processors)
    apply_extra_context(extra_context, c)
    return HttpResponse(t.render(c))


def object_detail(request,
                  cls,
                  query = {},
                  extra_context = {},
                  template_name = None,
                  template_name_field = None,
                  template_object_name = 'object',
                  template_loader = loader,
                  context_processors = None,
                  **kwargs
                 ):
    if callable(extra_context):
        extra_context = extra_context(request, **kwargs)

    if callable(query):
        query = query(request, **kwargs)

    object = cls.objects.find_one(query)

    if object is None:
        raise Http404, 'Object was not found in collection "%s"' % cls.collection.name()

    if not template_name:
        template_name = "%s_detail.html" % cls.objects.collection_name

    if template_name_field:
        template_name_list = [getattr(obj, template_name_field), template_name]
        t = template_loader.select_template(template_name_list)
    else:
        t = template_loader.get_template(template_name)

    c = RequestContext(request, {
            template_object_name: object,
        }, context_processors)
    apply_extra_context(extra_context, c)
    return HttpResponse(t.render(c))


def object_list(request,
                cls,
                query = {},
                paginate_by = None,
                page = None,
                allow_empty = True,
                template_name = None,
                template_loader = loader,
                extra_context = {},
                context_processors = None,
                template_object_name = 'object_list',
                mimetype = None,
                map_func = lambda x: x,
                **kwargs):
    """
    Generic list of objects.

    Templates: ``<collection_name>_list.html``
    Context:
        object_list
            list of objects
        is_paginated
            are the results paginated?
        results_per_page
            number of objects per page (if paginated)
        has_next
            is there a next page?
        has_previous
            is there a prev page?
        page
            the current page
        next
            the next page
        previous
            the previous page
        pages
            number of pages, total
        hits
            number of objects, total
        last_on_page
            the result number of the last of object in the
            object_list (1-indexed)
        first_on_page
            the result number of the first object in the
            object_list (1-indexed)
        page_range:
            A list of the page numbers (1-indexed).
    """
    if callable(extra_context):
        extra_context = extra_context(request, **kwargs)

    if callable(query):
        query = query(request, **kwargs)

    cursor = cls.objects.find(query)

    if paginate_by:
        paginator = Paginator(cursor, paginate_by, allow_empty_first_page=allow_empty)
        if not page:
            page = request.GET.get('page', 1)
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                # Page is not 'last', nor can it be converted to an int.
                raise Http404
        try:
            page_obj = paginator.page(page_number)
        except InvalidPage:
            raise Http404
        c = RequestContext(request, {
            template_object_name: map(map_func, page_obj.object_list),
            'paginator': paginator,
            'page_obj': page_obj,

            # Legacy template context stuff. New templates should use page_obj
            # to access this instead.
            'is_paginated': page_obj.has_other_pages(),
            'results_per_page': paginator.per_page,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page': page_obj.number,
            'next': page_obj.next_page_number(),
            'previous': page_obj.previous_page_number(),
            'first_on_page': page_obj.start_index(),
            'last_on_page': page_obj.end_index(),
            'pages': paginator.num_pages,
            'hits': paginator.count,
            'page_range': paginator.page_range,
        }, context_processors)
    else:
        c = RequestContext(request, {
            template_object_name: map(map_func, cursor),
            'paginator': None,
            'page_obj': None,
            'is_paginated': False,
        }, context_processors)
        if not allow_empty and len(cursor) == 0:
            raise Http404
    for key, value in extra_context.items():
        if callable(value):
            c[key] = value()
        else:
            c[key] = value
    if not template_name:
        template_name = "%s_list.html" % cls.objects.collection_name
    t = template_loader.get_template(template_name)
    return HttpResponse(t.render(c), mimetype=mimetype)



def commit(request, repository_slug, revision):
    mode = request.GET.get('mode', 'full')
    assert(mode in ('full', 'files'))

    file = request.GET.get('file', None)
    if file is not None:
        commit = Commit.objects.find_one(dict(
              slug = repository_slug,
              revision = revision)
        )
        if not commit:
            raise Http404, 'Object was not found in collection "%s"' % Commit.collection.name()

        obj = None
        for f in commit.changes.changed:
            if f.filename == file:
                obj = f
                break

        if obj is None:
            raise Http404, 'File %s was not found in commit "%s@%s"' % (file, commit.slug, commit.revision)

        return render_to_response(
          'django_vcs_watch/diff.html',
          dict(file = obj),
        )


    return object_detail(
            request,
            Commit,
            query = dict(slug = repository_slug, revision = revision),
            template_name = 'django_vcs_watch/commit_detail_%s.html' % mode,
        )


def get_user_feed(request):
    user = request.user
    feed_slug = get_user_feed_slug(user)
    return Feed.objects.find_one(dict(_id = feed_slug))


def refresh_feed(request, template_name = 'django_vcs_watch/refresh_feed.html'):
    feed = get_user_feed(request)
    feed.update()

    next = request.POST.get('next', None)
    if next is not None:
        return HttpResponseRedirect(next)

    return render_to_response(
        template_name,
        dict(feed = feed),
    )

def get_rule(request):
    rule_fields = ('author', 'slug')

    return dict(filter(
        lambda x: x[0] in rule_fields,
        request.POST.items()
    ))

@require_POST
def ignore(request):
    feed = get_user_feed(request)

    if feed.ignore is None:
        feed.ignore = []

    rule = get_rule(request)

    feed.ignore.append(rule)
    feed.save()

    if 'author' in rule:
        if 'slug' in rule:
            message = _('<div class="info">Now all commits from %(author)s in %(slug)s will be ignored. Boo-ga-ga!</div>')
        else:
            message = _('<div class="info">Now all commits from %(author)s will be ignored. Moo-ha-ha!</div>')
    else:
        message = _('<div class="error">Hm, it seems that we have no message for this case :).</div>')

    request.user.message_set.create(message = message % rule)

    next = request.POST.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', '/')

    return HttpResponseRedirect(next)


@require_POST
def unignore(request):
    feed = get_user_feed(request)

    if feed.ignore is None:
        feed.ignore = []

    rule = get_rule(request)

    if rule:
        feed.ignore = filter(lambda x: x != rule, feed.ignore)
    else:
        feed.ignore = []

    feed.save()

    if rule:
        request.user.message_set.create(message = _('Rule was removed.'))
    else:
        request.user.message_set.create(message = _('All rules were removed.'))

    next = request.POST.get('next', '/')
    return HttpResponseRedirect(next)


@require_POST
def watch(request):
    feed = get_user_feed(request)

    if feed.watch is None:
        feed.watch = []

    rule = get_rule(request)

    feed.watch.append(rule)
    feed.save()

    if 'slug' in rule:
        message = _('<div class="info">Now you watch on all commits to %(slug)s. Horay!</div>')
    elif 'author' in rule:
        message = _('<div class="info">Now you watch on all commits by %(author)s. Yee!</div>')
    else:
        message = _('<div class="error">Hm, it seems that we have no message for this case :).</div>')

    request.user.message_set.create(message = message % rule)

    next = request.POST.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', '/')

    return HttpResponseRedirect(next)


@require_POST
def unwatch(request):
    feed = get_user_feed(request)

    if feed.watch is None:
        feed.watch = []

    rule = get_rule(request)

    if rule:
        feed.watch = filter(lambda x: x != rule, feed.watch)
    else:
        feed.watch = []

    feed.save()

    if rule:
        request.user.message_set.create(message = _('Rule was removed.'))
    else:
        request.user.message_set.create(message = _('All rules were removed.'))

    next = request.POST.get('next', '/')
    return HttpResponseRedirect(next)

