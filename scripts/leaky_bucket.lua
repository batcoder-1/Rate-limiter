local user=KEYS[1]
local bucket_capacity=tonumber(ARGV[1])
local leakage_rate=tonumber(ARGV[2])
local time=redis.call("TIME")
local current_timestamp=time[1]+time[2]/1000000
local response=redis.call("HGET",user,"current_capacity")
local ttl_time=math.ceil(bucket_capacity/leakage_rate)+5

if response == false then
    redis.call("HSET",user,"current_capacity",1,"last_timestamp",current_timestamp)
    redis.call("EXPIRE",user,ttl_time)
    return true
else
    local current_capacity=tonumber(redis.call("HGET",user,"current_capacity"))
    local last_timestamp=tonumber(redis.call("HGET",user,"last_timestamp"))
    current_capacity=math.max(0,current_capacity-(current_timestamp-last_timestamp)*leakage_rate)
    if current_capacity < bucket_capacity then
        redis.call("HSET",user,"current_capacity",current_capacity+1,"last_timestamp",current_timestamp)
        redis.call("EXPIRE",user,ttl_time)
        return true
    end
    redis.call("HSET",user,"current_capacity",current_capacity,"last_timestamp",current_timestamp)
    redis.call("EXPIRE",user,ttl_time)
end
return false