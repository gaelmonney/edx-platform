"""
Define request handlers used by the zendesk_proxy djangoapp
"""
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from openedx.core.djangoapps.zendesk_proxy.utils import create_zendesk_ticket

ZENDESK_REQUESTS_PER_HOUR = 50


class ZendeskProxyThrottle(SimpleRateThrottle):
    """
    Custom throttle rates for this particular endpoint's use case.
    """
    def __init__(self):
        self.rate = '{}/hour'.format(ZENDESK_REQUESTS_PER_HOUR)
        super(ZendeskProxyThrottle, self).__init__()

    def get_cache_key(self, request, view):  # pylint: disable=unused-argument
        """
        By providing a static string here, we are limiting *all* users to the same combined limit.
        """
        return "ZendeskProxy_rate_limit_cache_key"


class ZendeskPassthroughView(APIView):
    """
    An APIView that will take in inputs from an unauthenticated endpoint, and use them to securely create a zendesk
    ticket.
    """
    throttle_classes = ZendeskProxyThrottle,
    parser_classes = JSONParser,

    def post(self, request):
        """
        request body is expected to look like this:
        {
            "requester": {
                "email": "john@example.com",
                "name": "name"
            },
            "subject": "test subject",
            "comment": {
                "body": "message details",
                "uploads": ['file_token'],
            },
            "custom_fields": [
                {
                    "id": '001',
                    "value": 'demo-course'
                }
            ],
            "tags": ["LMS"]
        }
        """
        try:
            proxy_status = create_zendesk_ticket(
                requester_name=request.data['requester']['name'],
                requester_email=request.data['requester']['email'],
                subject=request.data['subject'],
                body=request.data['comment']['body'],
                custom_fields=request.data['custom_fields'],
                tags=request.data['tags']
            )
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(
            status=proxy_status
        )
