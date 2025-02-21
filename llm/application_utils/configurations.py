import os

def update_config_from_env(configurations):
    try:
        configurations["llm_configurations"]["api_key"] = os.environ.get('GENERATIVE_MODEL_API_KEY')
        configurations["llm_configurations"]["model_endpoint"] = os.environ.get('GENERATIVE_MODEL_API')
        configurations["llm_configurations"]["model_name"] = os.environ.get('GENERATIVE_MODEL_NAME')

    except Exception as e:
        print(f"Custom Exception: - (update_config_from_env) {e}")
        configurations = {}
    return configurations