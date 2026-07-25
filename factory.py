from leaky_bucket import Leaky_Bucket
from sliding_window_counter import Sliding_Window_Counter
from sliding_window_log import Sliding_Window_Log
from token_bucket import Token_Bucket

def RateLimiter(algorithm,**kwargs):
    algo=algorithm.lower()
    if(algo=="leaky bucket"):
       return  Leaky_Bucket(**kwargs)
    elif(algo=="sliding window counter"):
         return Sliding_Window_Counter(**kwargs)
    elif(algo=="sliding window log"):
        return Sliding_Window_Log(**kwargs)
    elif(algo=="token bucket"):
        return  Token_Bucket(**kwargs)
    else:
        raise ValueError(f"Unknow algorithm {algorithm}")