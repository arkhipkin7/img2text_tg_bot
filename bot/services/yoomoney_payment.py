"""
Сервис для работы с платежами ЮMoney
"""
import logging
import uuid
from typing import Optional, Dict, Any
import aiohttp
import os

logger = logging.getLogger(__name__)


class YooMoneyPaymentService:
    """Сервис для работы с ЮMoney API"""
    
    def __init__(self):
        # Получаем настройки из переменных окружения
        self.shop_id = os.getenv("YOOMONEY_SHOP_ID")
        self.secret_key = os.getenv("YOOMONEY_SECRET_KEY")
        self.api_url = "https://api.yookassa.ru/v3"
        
        if not self.shop_id or not self.secret_key:
            logger.warning("ЮMoney credentials не настроены. Проверьте переменные YOOMONEY_SHOP_ID и YOOMONEY_SECRET_KEY")
    
    async def create_payment(
        self, 
        amount: float, 
        description: str,
        return_url: str,
        payment_method_type: str = "bank_card"
    ) -> Optional[Dict[str, Any]]:
        """
        Создание платежа
        
        Args:
            amount: Сумма в рублях
            description: Описание платежа
            return_url: URL для возврата после оплаты
            payment_method_type: Тип платежа (bank_card, sbp, yoo_money)
        
        Returns:
            Данные созданного платежа или None в случае ошибки
        """
        if not self.shop_id or not self.secret_key:
            logger.error("ЮMoney не настроен")
            return None
        
        payment_data = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": description,
            "payment_method_data": {
                "type": payment_method_type
            }
        }
        
        headers = {
            "Authorization": f"Basic {self.secret_key}",
            "Content-Type": "application/json",
            "Idempotence-Key": str(uuid.uuid4())
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/payments",
                    json=payment_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Платеж создан: {result['id']}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка создания платежа: {response.status} - {error_text}")
                        return None
        
        except Exception as e:
            logger.error(f"Исключение при создании платежа: {e}")
            return None
    
    async def check_payment_status(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Проверка статуса платежа
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Данные платежа или None в случае ошибки
        """
        if not self.shop_id or not self.secret_key:
            logger.error("ЮMoney не настроен")
            return None
        
        headers = {
            "Authorization": f"Basic {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/payments/{payment_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка проверки платежа: {response.status} - {error_text}")
                        return None
        
        except Exception as e:
            logger.error(f"Исключение при проверке платежа: {e}")
            return None
    
    def get_payment_method_type(self, method: str) -> str:
        """Конвертация внутреннего типа платежа в тип ЮMoney"""
        mapping = {
            "card": "bank_card",
            "sbp": "sbp", 
            "yoomoney": "yoo_money"
        }
        return mapping.get(method, "bank_card")
