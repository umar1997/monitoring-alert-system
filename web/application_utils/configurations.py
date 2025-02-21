import os

def update_config_from_env(configurations):
    try:
        configurations["web_configurations"]["subscription_key"] = os.environ.get('BING_SEARCH_SUBSCRIPTION_KEY')
        configurations["web_configurations"]["custom_config_id"] = os.environ.get('BING_SEARCH_CUSTOM_CONFIG_ID')
        configurations["web_configurations"]["bing_url"] = os.environ.get('BING_SEARCH_URL')

    except Exception as e:
        print(f"Custom Exception: - (update_config_from_env) {e}")
        configurations = {}
    return configurations