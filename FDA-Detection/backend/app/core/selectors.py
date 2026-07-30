"""
Shopee Scraper Selectors Configuration
This file stores all CSS selectors used by the scraper service.
Centralizing these constants allows for quick updates when Shopee changes its DOM structure which happens frequently.
"""

SH_SELECTORS = {
    # Homepage
    "POPUP_CLOSE_BUTTONS": [
        "div.shopee-popup__close-btn",
        "div[class*='close-btn']",
        "svg.shopee-svg-icon",
        "button[aria-label='Close']"
    ],
    
    # Search
    "SEARCH_BAR_INPUT": [
        ".shopee-searchbar-input__input",
        "input.shopee-searchbar-input__input",
        "input[aria-label='Search']",
        "input[placeholder*='ค้นหา']",
        "input[type='search']"
    ],
    
    # Search Results Page
    # Stratified selectors for robustness
    "SEARCH_RESULT_ITEM": [
        "div[data-sqe='item']",             # Standard stable attribute
        ".shopee-search-item-result__item", # Classic class
        "li[data-sqe='item']",
        "a[data-sqe='link']",               # Direct link container
        "div.col-xs-2-4",                   # Grid layout column
        "div[class*='search-item-result']"  # Fuzzy class match
    ],
    "SEARCH_RESULT_LINK": [
        "a[data-sqe='link']",
        "a"
    ],
    "SEARCH_ZERO_RESULT": [
        ".shopee-search-empty-result-section",
        "div[class*='no-result']"
    ],
    "SEARCH_RESULT_FALLBACK_IMAGE": "img",
    "SEARCH_RESULT_FALLBACK_TITLE": [
        "div[data-sqe='name']",
        ".shopee-search-item-result__item__name",
        "div[class*='item-card__name']"
    ],

    # Product Page
    "PRODUCT_TITLE": [
        ".att-attr-name", 
        "div._44qnta", 
        "span.mw-headline", 
        "h1", 
        "div.qaNIZv",
        ".product-briefing .att-attr-name"
    ],
    "PRODUCT_DESCRIPTION": [
        ".product-detail",
        "div._2C2YdY",
        "div[class*='product-detail']"
    ],
    "PRODUCT_IMAGE_CONTAINER": [
        ".UBG7wZ",          # New Thumbnail Class
        ".airUhU",          # New Gallery Container
        ".jA1mTx",          # Legacy Gallery Thumbnails
        ".UdI7e2"           # Featured Image
    ],
    "PRODUCT_IMAGE_NEXT_BUTTON": [
        "button.shopee-icon-button.nVAzDy.lWmpR1",
        "button.shopee-icon-button--right",
        ".shopee-icon-button"
    ],
    "PRODUCT_IMAGE_IMG_TAG": "img"
}
