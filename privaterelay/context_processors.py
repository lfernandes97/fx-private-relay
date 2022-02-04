from datetime import datetime, timedelta, timezone
from functools import lru_cache

from django.conf import settings

from .templatetags.relay_tags import premium_plan_price
from .utils import get_premium_countries_info_from_request


def django_settings(request):
    return {'settings': settings}

def common(request):
    fxa = _get_fxa(request)
    avatar = fxa.extra_data['avatar'] if fxa else None
    accept_language = request.headers.get('Accept-Language', 'en-US')
    country_code = request.headers.get('X-Client-Region', 'us').lower()
    premium_countries_vars = (
        get_premium_countries_info_from_request(request)
    )

    profile = request.user.profile_set.first()
    first_visit = request.COOKIES.get("first_visit")
    reason_to_show_csat_survey = None
    csat_dismissal_cookie = ""
    if (not request.user.is_anonymous and profile.has_premium and profile.date_subscribed):
        days_since_subscription = (datetime.now(timezone.utc) - profile.date_subscribed).days
        if (days_since_subscription >= 3 * 30):
            csat_dismissal_cookie = f'csat-survey-premium-90days_{profile.id}_dismissed'
            if (not request.COOKIES.get(csat_dismissal_cookie)):
                reason_to_show_csat_survey = "premium90days"
        elif (days_since_subscription >= 30):
            csat_dismissal_cookie = f'csat-survey-premium-30days_{profile.id}_dismissed'
            if (not request.COOKIES.get(csat_dismissal_cookie)):
                reason_to_show_csat_survey = "premium30days"
        elif (days_since_subscription >= 7):
            csat_dismissal_cookie = f'csat-survey-premium-7days_{profile.id}_dismissed'
            if (not request.COOKIES.get(csat_dismissal_cookie)):
                reason_to_show_csat_survey = "premium7days"
    elif (not request.user.is_anonymous and not profile.has_premium and first_visit):
        days_since_first_visit = (datetime.now(timezone.utc) - first_visit).days
        if (days_since_first_visit >= 3 * 30):
            csat_dismissal_cookie = f'csat-survey-free-90days_{profile.id}_dismissed'
            if (not request.COOKIES.get(csat_dismissal_cookie)):
                reason_to_show_csat_survey = "free90days"
        elif (days_since_first_visit >= 30):
            csat_dismissal_cookie = f'csat-survey-free-30days_{profile.id}_dismissed'
            if (not request.COOKIES.get(csat_dismissal_cookie)):
                reason_to_show_csat_survey = "free30days"
        elif (days_since_first_visit >= 7):
            csat_dismissal_cookie = f'csat-survey-free-7days_{profile.id}_dismissed'
            if (not request.COOKIES.get(csat_dismissal_cookie)):
                reason_to_show_csat_survey = "free7days"

    lang = accept_language.split(',')[0]
    lang_parts = lang.split("-") if lang and "-" in lang else [lang]
    lang = lang_parts[0].lower()
    show_csat = (reason_to_show_csat_survey is not None and (lang == 'en' or lang == 'fr' or lang == 'de'))

    common_vars = {
        'avatar': avatar,
        'ftl_mode': 'server',
        'accept_language': accept_language,
        'country_code': country_code,
        'show_csat': show_csat,
        'csat_dismissal_cookie': csat_dismissal_cookie,
        'monthly_price': premium_plan_price(
            accept_language, premium_countries_vars['country_code']
        ),
    }
    return {**common_vars, **premium_countries_vars}

@lru_cache(maxsize=None)
def _get_fxa(request):
    try:
        fxa = request.user.socialaccount_set.filter(provider='fxa').first()
        return fxa
    except AttributeError:
        return None
