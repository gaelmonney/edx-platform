"""
Learner analytics dashboard views
"""
import json
import logging
import urllib
from datetime import datetime, timedelta

import pytz
import requests
from analyticsclient.client import Client
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template.context_processors import csrf
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from opaque_keys.edx.keys import CourseKey
from util.views import ensure_valid_course_key
from xmodule.modulestore.django import modulestore

from lms.djangoapps.course_api.blocks.api import get_blocks
from lms.djangoapps.courseware.courses import get_course_with_access
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from openedx.features.course_experience import default_course_url_name

log = logging.getLogger(__name__)


class LearnerAnalyticsView(View):

    def __init__(self):
        View.__init__(self)
        self.analytics_client = Client(base_url=settings.ANALYTICS_API_URL, auth_token=settings.ANALYTICS_API_KEY)

    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    def get(self, request, course_id):
        """
        Displays the user's bookmarks for the specified course.

        Arguments:
            request: HTTP request
            course_id (unicode): course id
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        course_url_name = default_course_url_name(course.id)
        course_url = reverse(course_url_name, kwargs={'course_id': unicode(course.id)})

        # Render the course bookmarks page
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'course_url': course_url,
            'disable_courseware_js': True,
            'uses_pattern_library': True,
            'grading_policy': course.grading_policy,
            'assignment_grades': self.get_grade_data(request.user, course_key),
            'assignment_schedule': self.get_schedule(request, course_key),
            'weekly_active_users': self.get_weekly_course_activities(course_key),
            'day_streak': self.consecutive_active_days_for_user(request.user.username, course_key)
        }
        return render_to_response('learner_analytics/dashboard.html', context)

    def get_grade_data(self, user, course_key):
        """
        Collects and formats the grades data for a particular user and course.

        Args:
            user: User
            course_key: CourseKey
        """
        course_grade = CourseGradeFactory().read(user, course_key=course_key)
        grades = {}
        for (subsection, subsection_grade) in course_grade.subsection_grades.iteritems():
            grades[unicode(subsection)] = {
                'assignment_type': subsection_grade.format,
                'total_earned': subsection_grade.graded_total.earned,
                'total_possible': subsection_grade.graded_total.possible,
            }
        return json.dumps(grades)

    def get_discussion_data(self, user, course_key):
        """
        Collects and formats the discussion data from a particular user and course.

        Args:
            user: User
            course_key: CourseKey
        """
        pass

    def get_schedule(self, request, course_key):
        """
        Get the schedule of graded assignments in the course.

        Args:
            request: HttpRequest
            course_key: CourseKey
        """
        course_usage_key = modulestore().make_course_usage_key(course_key)
        all_blocks = get_blocks(
            request,
            course_usage_key,
            user=request.user,
            nav_depth=3,
            requested_fields=['display_name', 'due', 'graded', 'format'],
            block_types_filter=['sequential']
        )
        graded_blocks = {}
        for (location, block) in all_blocks['blocks'].iteritems():
            if block.get('graded', False) and block.get('due') is not None:
                graded_blocks[location] = block
                block['due'] = block['due'].isoformat()
        return json.dumps(graded_blocks)

    def get_weekly_course_activities(self, course_key):
        """
        Get the count of any course activity from previous 7 days

        Args:
            course_key: CourseKey
        """
        cache_key = 'learner_analytics_{course_key}_weekly_activities'.format(course_key=course_key)
        activities = cache.get(cache_key)

        if not activities:
            log.info('Weekly course activities for course {course_key} was not cached - fetching from Analytics API'
                     .format(course_key=course_key))
            activities = self.analytics_client.courses(course_key).activity()

            # activities should only have one item
            cache.set(cache_key, activities[0], LearnerAnalyticsView.seconds_to_cache_expiration())
            activities = activities[0]

        return activities['any']

    def consecutive_active_days_for_user(self, username, course_key):
        """
        Get the most recent count of consecutive days that a use has performed a course activity

        Args:
            username: Username
            course_key: CourseKey
        """
        cache_key = 'learner_dashboard_{username}_{course_key}_engagement_timeline'\
            .format(username=username, course_key=course_key)
        timeline = cache.get(cache_key)

        if not timeline:
            log.info('Engagement timeline for course {course_key} was not cached - fetching from Analytics API'
                     .format(course_key=course_key))

            # TODO: @jaebradley replace this once the Analytics client has an engagement timeline method
            url = "{base_url}/engagement_timelines/{username}?course_id={course_key}"\
                .format(base_url=settings.ANALYTICS_API_URL,
                        username=username,
                        course_key=urllib.quote_plus(course_key))
            headers = {"Authorization": "Token {token}".format(token=settings.ANALYTICS_API_KEY)}
            response = requests.get(url=url, headers=headers)
            data = response.json()

            # Analytics API returns data in ascending (by date) order - we want to count starting from most recent day
            data_ordered_by_date_descending = list(reversed(data['days']))

            cache.set(cache_key, data_ordered_by_date_descending, LearnerAnalyticsView.seconds_to_cache_expiration())
            timeline = data_ordered_by_date_descending

        return next((index for index, day in enumerate(timeline) if not LearnerAnalyticsView.has_activities(day)),
                    timeline.length)

    @staticmethod
    def has_activities(day):
        """
        Validate that a course had some activity that day

        Args:
            day: dictionary of activities and their counts
        """
        return day['problems_attempted'] > 0 \
            or day['problems_completed'] > 0 \
            or day['discussion_contributions'] > 0 \
            or day['videos_viewed'] > 0

    @staticmethod
    def seconds_to_cache_expiration():
        """Calculate cache expiration seconds. Currently set to seconds until midnight UTC"""
        next_midnight_utc = (datetime.today() + timedelta(days=1)).replace(hour=0, minute=0, second=0,
                                                                           microsecond=0, tzinfo=pytz.utc)
        now_utc = datetime.now(tz=pytz.utc)
        return round((next_midnight_utc - now_utc).total_seconds())
