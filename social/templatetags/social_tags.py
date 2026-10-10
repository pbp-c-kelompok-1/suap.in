from django import template

from social.models import Canteen

register = template.Library()


@register.inclusion_tag('social/partials/share_to_community.html', takes_context=True)
def community_share_form(context):
    """Form "Bagikan ke Community" yang disisipkan di halaman hasil scan."""
    request = context['request']
    result = request.session.get('scan_result') or {}
    names = [str(item.get('name', '')).strip() for item in result.get('detected_items', [])]
    return {
        'canteens': Canteen.objects.filter(is_active=True).order_by('faculty', 'name'),
        'default_food_name': ', '.join(n for n in names if n)[:100],
    }
