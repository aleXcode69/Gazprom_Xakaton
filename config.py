import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Проверяем, что все ключи загружены
def check_env_vars():
    missing_keys = []
    for i in range(1, 16):
        key = f'OPENROUTER_API_KEY_{i}'
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        raise EnvironmentError(f"Отсутствуют следующие переменные окружения: {', '.join(missing_keys)}")

# Проверяем переменные окружения при импорте
check_env_vars()

class OpenRouterConfig:
    API_KEYS: List[str] = [
        os.getenv('OPENROUTER_API_KEY_1'),
        os.getenv('OPENROUTER_API_KEY_2'),
        os.getenv('OPENROUTER_API_KEY_3'),
        os.getenv('OPENROUTER_API_KEY_4'),
        os.getenv('OPENROUTER_API_KEY_5'),
        os.getenv('OPENROUTER_API_KEY_6'),
        os.getenv('OPENROUTER_API_KEY_7'),
        os.getenv('OPENROUTER_API_KEY_8'),
        os.getenv('OPENROUTER_API_KEY_9'),
        os.getenv('OPENROUTER_API_KEY_10'),
        os.getenv('OPENROUTER_API_KEY_11'),
        os.getenv('OPENROUTER_API_KEY_12'),
        os.getenv('OPENROUTER_API_KEY_13'),
        os.getenv('OPENROUTER_API_KEY_14'),
        os.getenv('OPENROUTER_API_KEY_15')
    ]
    
    CURRENT_KEY_INDEX = 0
    MAX_RETRIES = 15  # Максимальное количество попыток
    
    @classmethod
    def get_current_key(cls) -> str:
        return cls.API_KEYS[cls.CURRENT_KEY_INDEX]
    
    @classmethod
    def rotate_key(cls) -> str:
        cls.CURRENT_KEY_INDEX = (cls.CURRENT_KEY_INDEX + 1) % len(cls.API_KEYS)
        return cls.get_current_key()
    
    @classmethod
    def get_all_keys(cls) -> List[str]:
        return cls.API_KEYS.copy() 
