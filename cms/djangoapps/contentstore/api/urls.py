""" Course Import API URLs. """
from django.conf import settings
from django.conf.urls import url

from cms.djangoapps.contentstore.api import views

urlpatterns = [
    url(r'^v0/import/{course_id}/$'.format(course_id=settings.COURSE_ID_PATTERN,),
        views.CourseImportView.as_view(), name='course_import'),
]
