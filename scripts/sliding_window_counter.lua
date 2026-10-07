local user=KEYS[1]
local window_size=tonumber(ARGV[1])
local rate_limit=tonumber(ARGV[2])
local time=redis.call("time")
local current_timestamp=time[1]+time[2]/1000000
local current_window_id=math.floor(current_timestamp/window_size)
local elapsed_fraction=(current_timestamp-current_window_id*window_size)/window_size
local response=redis.call("HGET",user,"previous_window_id")

if response == false then 
    redis.call("HSET",user,"previous_window_id",current_window_id,"current_count",1,"prev_count",0) -- first request will always gets accepted  
    redis.call("EXPIRE",user,2*window_size+1)
    return true
end

local prev_count=tonumber(redis.call("HGET",user,"prev_count"))
local current_count=tonumber(redis.call("HGET",user,"current_count"))
local previous_window_id=tonumber(redis.call("HGET",user,"previous_window_id"))

if current_window_id == previous_window_id then
    local elapsed_requests=(1-elapsed_fraction)*prev_count+current_count
    if elapsed_requests < rate_limit then 
        redis.call("HSET",user,"current_count",current_count+1)
        redis.call("EXPIRE",user,2*window_size+1)
        return true
    end
     redis.call("EXPIRE",user,2*window_size+1)
    return false
elseif current_window_id == previous_window_id+1 then
    prev_count=current_count
    current_count=0
    local elapsed_requests=(1-elapsed_fraction)*prev_count+current_count
    if elapsed_requests < rate_limit then 
        redis.call("HSET",user,"previous_window_id",current_window_id,"current_count",current_count+1,"prev_count",prev_count)
         redis.call("EXPIRE",user,2*window_size+1)
        return true
    end
    redis.call("HSET",user,"previous_window_id",current_window_id,"current_count",current_count,"prev_count",prev_count)
     redis.call("EXPIRE",user,2*window_size+1)
    return false
else
    prev_count=0
    current_count=0
     local elapsed_requests=(1-elapsed_fraction)*prev_count+current_count
     if elapsed_requests < rate_limit then 
        redis.call("HSET",user,"previous_window_id",current_window_id,"current_count",current_count+1,"prev_count",prev_count)
         redis.call("EXPIRE",user,2*window_size+1)
        return true
    end
    redis.call("HSET",user,"previous_window_id",current_window_id,"current_count",current_count,"prev_count",prev_count)
     redis.call("EXPIRE",user,2*window_size+1)
    return false
end
