from functools import wraps
def trace_decorator(function):
    @wraps(function)
    def wrapped(one_arg):
        print("Start %s", function.__qualname__)
        return function(one_arg)
    
    return wrapped
@trace_decorator
def process_account(account_id):
    print("Process account")

print(process_account.__qualname__) #trace_decorator.<locals>.wrapped
