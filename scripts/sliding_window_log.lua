local user=KEYS[1]
local rate_limit=tonumber(ARGV[1])
local window_size=tonumber(ARGV[2])
local time=redis.call("TIME")
local current_timestamp=time[1]+time[2]/1000000
redis.call("zremrangebyscore",user,"-inf",current_timestamp-window_size) -- delete 
local cnt=redis.call("zcard",user)-- counter for member uniqueness in set
if cnt < rate_limit then
    local counter=redis.call("incr",user.."-seq")
    redis.call("zadd",user,current_timestamp,counter)
    redis.call("expire",user,window_size)
    redis.call("expire",user.."-seq",window_size)
    return true
end
redis.call("expire",user,window_size)
redis.call("expire",user.."-seq",window_size)
return false -- not storing any persistent key even after rejection 
