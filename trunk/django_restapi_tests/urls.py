from django.conf.urls.defaults import *
from django_restapi.model_resource import Collection, Entry
from django_restapi.responder import *
from django_restapi.authentication import *
from polls.models import Poll, Choice

urlpatterns = patterns('',
   ( r'^admin/', include('django.contrib.admin.urls')),
)

# Really simple XML example.
#
# URLs are generated automatically:
# The API is available at /api/poll/, /api/poll/[poll_id]/,
# /api/choice/ and /api/choice/[choice_id]/

simple_poll_resource = Collection(
    queryset = Poll.objects.all(), 
    responder = XMLResponder(),
)
simple_choice_resource = Collection(
    queryset = Choice.objects.all(),
    responder = XMLResponder()
)

urlpatterns += simple_poll_resource.get_url_pattern()
urlpatterns += simple_choice_resource.get_url_pattern()


# XML Test API URLs
#
# URLs are generated semi-automatically (base_url given):
# The API is available at /xml/polls/, /xml/polls/[poll_id]/,
# /xml/choices/ and /xml/choices/[choice_id]/

xml_poll_resource = Collection(
    queryset = Poll.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ('id', 'question', 'pub_date'),
    responder = XMLResponder(paginate_by = 10),
    collection_url_pattern = r'^xml/polls/?$'
)

xml_choice_resource = Collection(
    queryset = Choice.objects.all(),
    permitted_methods = ('GET',),
    expose_fields = ('id', 'poll_id', 'choice'),
    responder = XMLResponder(paginate_by = 5),
    collection_url_pattern = r'^xml/choices/?$'
)

urlpatterns += xml_poll_resource.get_url_pattern()
urlpatterns += xml_choice_resource.get_url_pattern()


# Template Test API URLs
#
# URLs are generated semi-automatically (base_url given):
# The API is available at /html/polls/, /html/polls/[poll_id]/,
# /html/choices/ and /html/choices/[choice_id]/

template_poll_resource = Collection(
    queryset = Poll.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ('id', 'question', 'pub_date'),
    responder = TemplateResponder(
        template_dir = 'polls',
        template_object_name = 'poll',
        paginate_by = 10
    ),
    collection_url_pattern = r'^html/polls/?$'
)

template_choice_resource = Collection(
    queryset = Choice.objects.all(),
    permitted_methods = ('GET',),
    expose_fields = ('id', 'poll_id', 'choice'),
    responder = TemplateResponder(
        template_dir = 'polls',
        template_object_name = 'choice',
        paginate_by = 5
    ),
    collection_url_pattern = r'^html/choices/?$'
)

urlpatterns += template_poll_resource.get_url_pattern()
urlpatterns += template_choice_resource.get_url_pattern()


# JSON Test API URLs
#
# Polls are available at /json/polls/ and 
# /json/polls/[poll_id]/.
#
# Different (manual) URL structure for choices:
# /json/polls/[poll_id]/choices/[number of choice]/
# Example: /json/polls/121/choices/2/ identifies the second 
# choice for the poll with ID 121.

json_poll_resource = Collection(
    queryset = Poll.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ('id', 'question', 'pub_date'),
    responder = JSONResponder(paginate_by=10),
    collection_url_pattern = r'^json/polls/$'
)

class ChoiceCollection(Collection):
    
    def read(self, request, url_parts={}):
        filtered_set = self.queryset._clone()
        filtered_set = filtered_set.filter(poll__id=int(url_parts['poll_id']))
        return self.responder.list(request, filtered_set)
    
    def get_entry(self, url_parts):
        poll_id = url_parts.get('poll_id')
        choice_num = url_parts.get('choice_num')
        if poll_id and choice_num:
            poll = Poll.objects.get(id=int(poll_id))
            choice = poll.get_choice_from_num(int(choice_num))
            return Entry(self, choice)
        return None

    def get_entry_url(self, entry):
        choice_num = entry.model.get_num()
        return 'json/polls/%d/choices/%s/' % (entry.model.poll.id, choice_num)

json_choice_resource = ChoiceCollection(
    queryset = Choice.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ('id', 'poll_id', 'choice', 'votes'),
    responder = JSONResponder(paginate_by=5),
    collection_url_pattern = r'^json/polls/(?P<poll_id>\d+)/choices/?$',
    entry_url_pattern = r'^json/polls/(?P<poll_id>\d+)/choices/(?P<choice_num>\d+)/?$'
)

urlpatterns += json_poll_resource.get_url_pattern()
urlpatterns += json_choice_resource.get_url_pattern()


# Authentication Test API URLs
#
# URLs are generated automatically:
# The API is available at /basic/poll/s, /basic/polls/[poll_id]/,
# /digest/polls/ and /digest/polls/[poll_id]/

def digest_authfunc(username, realm):
    """
    Exemplary authfunc for HTTP Digest. In production situations,
    the combined hashes of realm, username and password are usually
    stored in a special file/db.
    """
    hashes = {
        ('realm1', 'john') : '3014aff1d0d0f0038e23c1195301def3', # Password: johnspass
        ('realm2', 'jim') : '5bae77fe607e161b831c8f8026a2ceb2'   # Password: jimspass
    }
    return hashes.get((username, realm), "")

# No auth function for HTTP Basic specified
# -> django.contrib.auth.models.User is used.
# Test with username 'rest', password 'rest'.
basicauth_poll_resource = Collection(
    queryset = Poll.objects.all(), 
    responder = XMLResponder(),
    authentication = HttpBasicAuthentication(),
    collection_url_pattern = r'^basic/polls/$'
)
digestauth_poll_resource = Collection(
    queryset = Poll.objects.all(),
    responder = XMLResponder(),
    authentication = HttpDigestAuthentication(digest_authfunc, 'realm1'),
    collection_url_pattern = r'^digest/polls/$'
)

urlpatterns += basicauth_poll_resource.get_url_pattern()
urlpatterns += digestauth_poll_resource.get_url_pattern()