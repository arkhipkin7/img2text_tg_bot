"""
Единственный источник правды для тарифов/цен и лимитов.
Меняйте значения здесь — бот подхватит при перезапуске.
"""

PRICING = {
    "free_requests": 3,
    "plans": [
        {
            "code": "10", 
            "quota": 10, 
            "price_rub": 180, 
            "label": "🌱 Стартер", 
            "description": "180₽ / 10 запросов",
            "price_per_request": 18,
            "brief": "Для начала и теста",
            "recommended": False,
            "benefits": "Подходит для знакомства с сервисом"
        },
        {
            "code": "30", 
            "quota": 30, 
            "price_rub": 509, 
            "label": "🚀 Прорыв", 
            "description": "509₽ / 30 запросов",
            "price_per_request": 17,
            "brief": "Больше выгоды при небольшом увеличении",
            "recommended": False,
            "benefits": "Экономия 1₽ за запрос по сравнению со Стартером"
        },
        {
            "code": "100", 
            "quota": 100, 
            "price_rub": 1599, 
            "label": "⭐ Профи", 
            "description": "1599₽ / 100 запросов",
            "price_per_request": 16,
            "brief": "Оптимально по цене и объёму",
            "recommended": True,
            "benefits": "★ Самый выгодный выбор! Экономия 2₽ за запрос"
        },
        {
            "code": "250", 
            "quota": 250, 
            "price_rub": 3747, 
            "label": "💎 Премиум", 
            "description": "3747₽ / 250 запросов",
            "price_per_request": 15,
            "brief": "Для активного бизнеса",
            "recommended": False,
            "benefits": "Экономия 3₽ за запрос. Подходит для среднего бизнеса"
        },
        {
            "code": "500", 
            "quota": 500, 
            "price_rub": 6994, 
            "label": "👑 Император", 
            "description": "6994₽ / 500 запросов",
            "price_per_request": 14,
            "brief": "Для корпоративных клиентов",
            "recommended": False,
            "benefits": "Экономия 4₽ за запрос. Максимальная выгода"
        },
        {
            "code": "1000", 
            "quota": 1000, 
            "price_rub": 12999, 
            "label": "🌟 Мастер", 
            "description": "12999₽ / 1000 запросов",
            "price_per_request": 13,
            "brief": "Для агентств и крупного ритейла",
            "recommended": False,
            "benefits": "Экономия 5₽ за запрос. Лучшая цена для больших объёмов"
        },
    ],
    "one_time": {
        "count": 1, 
        "price_rub": 20, 
        "label": "⚡ Разовый", 
        "description": "20₽ / 1 запрос",
        "price_per_request": 20,
        "brief": "Для разовых задач",
        "benefits": "Попробуйте без обязательств"
    },
}

def get_plan_quota_map() -> dict:
    """Возвращает словарь {code: quota} для планов."""
    return {str(p["code"]): int(p["quota"]) for p in PRICING.get("plans", [])}


