from base import BaseClass

class Token_Bucket(BaseClass):
    bucket_capacity:int
    refill_rate:float
    def __init__(self,bucket_capacity,refill_rate):
        self.bucket_capacity=bucket_capacity
        self.refill_rate=refill_rate
       