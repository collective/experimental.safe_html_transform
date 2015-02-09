import logging

from Products.ATContentTypes.content import link

logger = logging.getLogger('ATContentTypes')
logger.log(logging.INFO, 'Warning: You have content instances of the '
    'ATFavorite type in your site. This type is no longer available. Please '
    'remove all remaining instances of this type or migrate them to links.')


class ATFavorite(link.ATLink):
    """BBB: The old and long removed favorite content type."""

    portal_type = 'Favorite'
    archetype_name = 'Favorite'
