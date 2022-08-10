# Decorator

> 데코레이터는 DRY 원칙을 따라 코드를 잘 정돈되게 하지만, 
> 신중하게 설계되지 않으면 코드의 복잡성을 증가시킬 수 있다.

## Decorator 사용 원칙

- 처음부터 데코레이터를 만들지 않는다. 패턴이 생기고 데코레이터에 대한 추상화가 명확해지면 그 때 리팩토링을 한다.
- 데코레이터가 적어도 3회 이상 필요한 경우에만 구현한다.
- 데코레이터 코드를 최소한으로 유지한다.

## Function Decorator

```python
def retry(operation):
    @wraps(operation)
    def wrapped(*args, **kwargs):
        last_raised = None
        RETRIES_LIMIT = 3
        for _ in range(RETRIES_LIMIT):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_raised = e
        raise last_raised

    return wrapped

@retry
def run_operation(task):
    return task.run()

#@retry is Syntactic sugar which is equal to
run_operation = retry(run_operation)
```

### Decorator with args

> 함수를 한 단계 더 중첩한다

```python
#첫 번째 함수는 파라미터를 받아서 내부 함수에 전달
#두 번째 함수는 데코레이터가 되는 함수
#세 번째 함수는 데코레이팅 결과를 반환하는 함수
RETRIES_LIMIT = 3
def with_retry(retries_limit=RETRIES_LIMIT, allowed_exceptions=None):
    allowed_exceptions = allowed_exceptions or (Exception,)

    def retry(operation):

        @wraps(operation)
        def wrapped(*args, **kwargs):
            last_raised = None
            for _ in range(retries_limit):
                try:
                    return operation(*args, **kwargs)
                except allowed_exceptions as e:
                    last_raised = e
            raise last_raised

        return wrapped
    
    return retry

@with_retry(retries_limit=2) 
def run_operation(task):
    return task.run()

#run_operation = with_retry(retries_limit=2)(run_operation)


#class 버전
class WithRetry:

    def __init__(self, retries_limit=RETRIES_LIMIT, allowed_exceptions=None):
        self.retries_limit = retries_limit
        self.allowed_exceptions = allowed_exceptions or (Exception,)


    def __call____(self, operation):

        def retry(operation):

            @wraps(operation)
            def wrapped(*args, **kwargs):
                last_raised = None
                for _ in range(retries_limit):
                    try:
                        return operation(*args, **kwargs)
                    except allowed_exceptions as e:
                        last_raised = e
                raise last_raised
    
            return wrapped
        
        return retry

@WithRetry(retries_limit=5)
def run_with_custom_retries_limit(task):
    return task.run()

#run_with_custom_retries_limit = WithRetry(retries_limit=5)(run_with_custom_retries_limit)
```

## Class Decorator

```python
from datetime import datetime

def hide_field(field):
    return "**민감한 정보 삭제**"

def format_time(field_timestamp):
    return field_timestamp.strftime("%Y-%m-%d %H:%M")

def show_original(event_field):
    return event_field

class EventSerializer:
    def __init__(self, serialization_field):
        self.serialization_fields = serialization_fields
    
    def serialize(self, event):
        return {
            field: transformation(getattr(event, field))
            for field, transformation in
            self.serialization_fields.items()
        }

class Serialization:
    def __init__(self, **transformations):
        self.serializer = EventSerializer(transformations)

    def __call__(self, event_class):
        def serialize_method(event_instance):
            return self.serializer.serialize(event_instance)
        event_class.serialize = serialize_method
        return event_class


@Serialization(
    username=show_original,
    password=hide_field,
    ip=show_original,
    timestamp=format_time
    )
class LoginEvent:

    def __init__(self, username, password, ip, timestamp):
        self.username = username
        self.password = password
        self.ip = ip
        self.timestamp = timestamp


#if python >= 3.7(PEP-557)
@Serialization(
    username=show_original,
    password=hide_field,
    ip=show_original,
    timestamp=format_time
    )
@dataclass  #데코레이터는 함수, 메서드, 클래스뿐만 아니라 제너레이터, 코루틴, 이미 데코레이트된 객체도 데코레이트 가능하다.
class LoginEvent:
    username: str
    password: str
    ip: str
    timestamp: datetime
```

## Why do we use @wraps?

> It is useful for logging & debugging

```python
from functools import wraps

#without @wraps
def trace_decorator(function):
    #@wraps(function)
    def wrapped(one_arg):
        print("Start %s", function.__qualname__)
        return function(one_arg)
    
    return wrapped
@trace_decorator
def create_account(account_id):
    print("Create account")

@trace_decorator
def remove_account(account_id):
    print("Remove account")

print(process_account.__qualname__) #trace_decorator.<locals>.wrapped
print(remove_account.__qualname__) #trace_decorator.<locals>.wrapped


#with @wraps
def trace_decorator(function):
    @wraps(function)
    #...

print(process_account.__qualname__) #process_account
print(remove_account.__qualname__) #remove_account
```

## Decorator with SRP
> Decorator도 class, function 등과 동일하게 SRP를 지켜야한다.

```python
#Violate SRP
def traced_function(function):
    @wraps(function)
    def wrapped():
        print("Start %s", function.__qualname__)
        start_time = time.time()
        result = function()
        print("%s took %.2fs ", function.__qualname__, time.time() - start_time)
        return result
    return wrapped

#Keep SRP
def log_execution(function):
    @wraps(function)
    def wrapped():
        print("Start %s", function.__qualname__)
        return function()
    return wrapped

def measure_time(function):
    @wraps(function)
    def wrapped():
        start_time = time.time()
        result = function()
        print("%s took %.2fs ", function.__qualname__, time.time() - start_time)
        return result
    return wrapped

@measure_time
@log_execution
def operation():
    #...

```
