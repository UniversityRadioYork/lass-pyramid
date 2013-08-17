"""Nose tests for the Website submodule."""
import functools
import nose.tools

import lass.website.views


def test_signup_validate_create():
    """Tests lass.website.views.signup_validate_create."""
    exception = lass.website.views.SignupError
    validate = lass.website.views.signup_validate_create

    # Mock API configuration
    config = {
        ('param-' + key): ('bonzo-dog-' + key) for key in (
            'api-key',
            'first-name',
            'last-name',
            'email',
            'gender',
            'college'
        )
    }
    config['api-key'] = '11-11-11'

    assert_signup_error = functools.partial(
        nose.tools.assert_raises,
        exception,
        validate,
        config
    )

    valid_params = {
        'first-name': 'John',
        'last-name': 'Egbert',
        'email': 'je413',
        'gender': 'm',
        'college': '1'
    }

    def check_payload(payload):
        check = dict(valid_params)
        check['api-key'] = config['api-key']
        assert all(
            (
                payload[config['param-' + key]] == check[key]
                for key in check
            )
        ), 'Retrieved an incorrect payload from the validator.'

    #
    # Tests proper
    #

    # The above should work:
    payload = validate(config, valid_params)
    check_payload(payload)


    # Make sure adding leading or trailing space to the parameters
    # doesn't affect their validity.
    leading_spaces = {
        key: ('   ' + value) for key, value in valid_params.items()
    }
    payload = validate(config, leading_spaces)
    check_payload(payload)

    trailing_spaces = {
        key: (value + '   ') for key, value in valid_params.items()
    }
    payload = validate(config, trailing_spaces)
    check_payload(payload)

    # Make sure removing any of the parameters causes an error.
    for key in valid_params:
        missing_param = dict(valid_params)
        del missing_param[key]
        assert_signup_error(missing_param)

    # Make sure blanking out any of the params causes an error too.
    for key in valid_params:
        blank_param = dict(valid_params)
        blank_param[key] = ''
        assert_signup_error(blank_param)

    # Make sure a silly gender is rejected.
    # (No gender bias or discrimination is intended in this code.)
    bad_gender = dict(valid_params)
    bad_gender['gender'] = 'piano'
    assert_signup_error(bad_gender)

    # Make sure a non-integer college is rejected.
    bad_college = dict(valid_params)
    bad_college['college'] = 'horse'
    assert_signup_error(bad_college)
