define([
    'backbone',
    'jquery',
    'js/staff_debug_actions',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'
],
    function(Backbone, $, tmp, AjaxHelpers) {
        'use strict';
        var StaffDebug = window.StaffDebug;

        describe('StaffDebugActions', function() {
            var location = 'i4x://edX/Open_DemoX/edx_demo_course/problem/test_loc';
            var locationName = 'test_loc';
            var usernameFixtureID = 'sd_fu_' + locationName;
            var $usernameFixture = $('<input>', {id: usernameFixtureID, placeholder: 'userman'});
            var scoreFixtureID = 'sd_fs_' + locationName;
            var $scoreFixture = $('<input>', {id: scoreFixtureID, placeholder: '0'});
            var escapableLocationName = 'test\.\*\+\?\^\:\$\{\}\(\)\|\]\[loc';
            var escapableFixtureID = 'sd_fu_' + escapableLocationName;
            var $escapableFixture = $('<input>', {id: escapableFixtureID, placeholder: 'userman'});
            var esclocationName = 'P2:problem_1';
            var escapableId = 'result_' + esclocationName;
            var $escapableResultArea = $('<div>', {id: escapableId});

            describe('getURL ', function() {
                it('defines url to courseware ajax entry point', function() {
                    spyOn(StaffDebug, 'getCurrentUrl')
                      .and.returnValue('/courses/edX/Open_DemoX/edx_demo_course/courseware/stuff');
                    expect(StaffDebug.getURL('rescore_problem'))
                      .toBe('/courses/edX/Open_DemoX/edx_demo_course/instructor/api/rescore_problem');
                });
            });

            describe('sanitizeString', function() {
                it('escapes escapable characters in a string', function() {
                    expect(StaffDebug.sanitizeString('.*+?^:${}()|]['))
                      .toBe('\\.\\*\\+\\?\\^\\:\\$\\{\\}\\(\\)\\|\\]\\[');
                });
            });

            describe('getUser', function() {
                it('gets the placeholder username if input field is empty', function() {
                    $('body').append($usernameFixture);
                    expect(StaffDebug.getUser(locationName)).toBe('userman');
                    $('#' + usernameFixtureID).remove();
                });
                it('gets a filled in name if there is one', function() {
                    $('body').append($usernameFixture);
                    $('#' + usernameFixtureID).val('notuserman');
                    expect(StaffDebug.getUser(locationName)).toBe('notuserman');

                    $('#' + usernameFixtureID).val('');
                    $('#' + usernameFixtureID).remove();
                });
                it('gets the placeholder name if the id has escapable characters', function() {
                    $('body').append($escapableFixture);
                    expect(StaffDebug.getUser('test.*+?^:${}()|][loc')).toBe('userman');
                    $("input[id^='sd_fu_']").remove();
                });
            });
            describe('getScore', function() {
                it('gets the placeholder score if input field is empty', function() {
                    $('body').append($scoreFixture);
                    expect(StaffDebug.getScore(locationName)).toBe('0');
                    $('#' + scoreFixtureID).remove();
                });
                it('gets a filled in score if there is one', function() {
                    $('body').append($scoreFixture);
                    $('#' + scoreFixtureID).val('1');
                    expect(StaffDebug.getScore(locationName)).toBe('1');

                    $('#' + scoreFixtureID).val('');
                    $('#' + scoreFixtureID).remove();
                });
            });
            describe('doInstructorDashAction success', function() {
                it('adds a success message to the results element after using an action', function() {
                    $('body').append($escapableResultArea);
                    var requests = AjaxHelpers.requests(this);
                    var action = {
                        locationName: esclocationName,
                        success_msg: 'Successfully reset the attempts for user userman'
                    };
                    StaffDebug.doInstructorDashAction(action);
                    AjaxHelpers.respondWithJson(requests, action);
                    expect($('#idash_msg').text()).toBe('Successfully reset the attempts for user userman');
                    $('#result_' + locationName).remove();
                });
            });
            describe('doInstructorDashAction error', function() {
                it('adds a failure message to the results element after using an action', function() {
                    $('body').append($escapableResultArea);
                    var requests = AjaxHelpers.requests(this);
                    var action = {
                        locationName: esclocationName,
                        error_msg: 'Failed to reset attempts for user.'
                    };
                    StaffDebug.doInstructorDashAction(action);
                    AjaxHelpers.respondWithTextError(requests);
                    expect($('#idash_msg').text()).toBe('Failed to reset attempts for user. ');
                    $('#result_' + locationName).remove();
                });
            });
            describe('reset', function() {
                it('makes an ajax call with the expected parameters', function() {
                    $('body').append($usernameFixture);

                    spyOn($, 'ajax');
                    StaffDebug.reset(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        problem_to_reset: location,
                        unique_student_identifier: 'userman',
                        delete_module: false,
                        only_if_higher: undefined,
                        score: undefined
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/reset_student_attempts'
                    );
                    $('#' + usernameFixtureID).remove();
                });
            });
            describe('deleteStudentState', function() {
                it('makes an ajax call with the expected parameters', function() {
                    $('body').append($usernameFixture);

                    spyOn($, 'ajax');
                    StaffDebug.deleteStudentState(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        problem_to_reset: location,
                        unique_student_identifier: 'userman',
                        delete_module: true,
                        only_if_higher: undefined,
                        score: undefined
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/reset_student_attempts'
                    );

                    $('#' + usernameFixtureID).remove();
                });
            });
            describe('rescore', function() {
                it('makes an ajax call with the expected parameters', function() {
                    $('body').append($usernameFixture);

                    spyOn($, 'ajax');
                    StaffDebug.rescore(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        problem_to_reset: location,
                        unique_student_identifier: 'userman',
                        delete_module: undefined,
                        only_if_higher: false,
                        score: undefined
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/rescore_problem'
                    );
                    $('#' + usernameFixtureID).remove();
                });
            });
            describe('rescoreIfHigher', function() {
                it('makes an ajax call with the expected parameters', function() {
                    $('body').append($usernameFixture);

                    spyOn($, 'ajax');
                    StaffDebug.rescoreIfHigher(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        problem_to_reset: location,
                        unique_student_identifier: 'userman',
                        delete_module: undefined,
                        only_if_higher: true,
                        score: undefined
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/rescore_problem'
                    );
                    $('#' + usernameFixtureID).remove();
                });
            });
            describe('overrideScore', function() {
                it('makes an ajax call with the expected parameters', function() {
                    $('body').append($usernameFixture);
                    $('body').append($scoreFixture);
                    $('#' + scoreFixtureID).val('1');
                    spyOn($, 'ajax');
                    StaffDebug.overrideScore(locationName, location);

                    expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                    expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                        problem_to_reset: location,
                        unique_student_identifier: 'userman',
                        delete_module: undefined,
                        only_if_higher: undefined,
                        score: '1'
                    });
                    expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                        '/instructor/api/override_problem_score'
                    );
                    $('#' + usernameFixtureID).remove();
                });
            });
        });
    });
