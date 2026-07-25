import redis
from abc import ABC,abstractmethod
class BaseClass(ABC):
    redis_client:redis.Redis
    nameSpace:str
    def __init__(self,redis_client,nameSpace):
        self.redis_client=redis_client
        self.nameSpace=nameSpace
        
    @abstractmethod 
    def isAllow(self,user_id)->bool:
        ... 