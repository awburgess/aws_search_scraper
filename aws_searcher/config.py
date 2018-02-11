"""
Configuration file for global variables and settings
"""
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) ' \
             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'

# noss id is always 1 or 2
AMAZON_SEARCH_URL_TEMPLATE = "https://www.amazon.com/s/ref=" \
                             "nb_sb_noss_{noss_id}?url={category}&field-keywords={search}"

CATEGORIES_DICT = {'Alexa Skills': 'search-alias=alexa-skills',
                   'All Departments': 'search-alias=aps',
                   'Amazon Devices': 'search-alias=amazon-devices',
                   'Amazon Video': 'search-alias=instant-video',
                   'Amazon Warehouse Deals': 'search-alias=warehouse-deals',
                   'Appliances': 'search-alias=appliances',
                   'Apps & Games': 'search-alias=mobile-apps',
                   'Arts, Crafts & Sewing': 'search-alias=arts-crafts',
                   'Automotive Parts & Accessories': 'search-alias=automotive',
                   'Baby': 'search-alias=fashion-baby',
                   'Beauty & Personal Care': 'search-alias=beauty',
                   'Books': 'search-alias=stripbooks',
                   'Boys': 'search-alias=fashion-boys',
                   'CDs & Vinyl': 'search-alias=popular',
                   'Cell Phones & Accessories': 'search-alias=mobile',
                   'Clothing, Shoes & Jewelry': 'search-alias=fashion',
                   'Collectibles & Fine Art': 'search-alias=collectibles',
                   'Computers': 'search-alias=computers',
                   'Courses': 'search-alias=courses',
                   'Credit and Payment Cards': 'search-alias=financial',
                   'Digital Music': 'search-alias=digital-music',
                   'Electronics': 'search-alias=electronics',
                   'Garden & Outdoor': 'search-alias=lawngarden',
                   'Gift Cards': 'search-alias=gift-cards',
                   'Girls': 'search-alias=fashion-girls',
                   'Grocery & Gourmet Food': 'search-alias=grocery',
                   'Handmade': 'search-alias=handmade',
                   'Health, Household & Baby Care': 'search-alias=hpc',
                   'Home & Business Services': 'search-alias=local-services',
                   'Home & Kitchen': 'search-alias=garden',
                   'Industrial & Scientific': 'search-alias=industrial',
                   'Kindle Store': 'search-alias=digital-text',
                   'Luggage & Travel Gear': 'search-alias=fashion-luggage',
                   'Luxury Beauty': 'search-alias=luxury-beauty',
                   'Magazine Subscriptions': 'search-alias=magazines',
                   'Men': 'search-alias=fashion-mens',
                   'Movies & TV': 'search-alias=movies-tv',
                   'Musical Instruments': 'search-alias=mi',
                   'Office Products': 'search-alias=office-products',
                   'Pet Supplies': 'search-alias=pets',
                   'Prime Exclusive Savings': 'search-alias=prime-exclusive',
                   'Prime Pantry': 'search-alias=pantry',
                   'Software': 'search-alias=software',
                   'Sports & Outdoors': 'search-alias=sporting',
                   'Tools & Home Improvement': 'search-alias=tools',
                   'Toys & Games': 'search-alias=toys-and-games',
                   'Vehicles': 'search-alias=vehicles',
                   'Video Games': 'search-alias=videogames',
                   'Women': 'search-alias=fashion-womens'}
