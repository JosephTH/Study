# Descriptor

- 디스크립터는 코드 중복을 피하기 위한 강력한 추상화 도구이다.
- 프로퍼티가 필요한 구조가 반복되는 경우, 디스크립터는 좋은 해결책이 될 수 있다.
- 비즈니스 로직을 넣어선 안되고, 내부 API 전용으로 사용하는 것이 좋다.
- 실질적인 코드 반복의 증거가 없거나 복잡성의 대가가 명확하지 않다면 굳이 디스크립터를 사용할 필요가 없다.

## __get\_\_(self, instance, owner)

- 디스크립터 속성에 접근할 때 호출됨
- **instance**: 디스크립터를 호출한 객체
- **owner**: 해당 객체의 클래스
  - instance.__class__를 사용하면 되는데, 왜 owner를 parameter로 받아야 하지?
  - => Class에서 디스크립터를 호출할 경우, instance 값은 None임

```python
class DescriptorClass(object):
    def __get__(self, instance, owner):
        if instance is None:
            return '%s.%s' % (self.__class__.__name__, owner.__name__)
        return 'value for %s' % instance

class ClientClass(object):
    descriptor = DescriptorClass()

print(ClientClass.descriptor) #DescriptorClass.ClientClass
print(ClientClass().descriptor) #value for <__main__.ClientClass object at 0x7fad4bf618d0>

```

## __set\_\_(self, instance, value)

- 디스크립터에 값을 할당하려고 할 때 호출된다.
- **__set__을 구현하지 않을 경우**, client.descriptor = "value"는 "value"는 descriptor 자체를 덮어쓴다.
- **self.attr = value**를 사용하면, 디스크립터를 사용하는 모든 객체에서 동일한 값에 접근하게 된다.
- 그러므로 instance.**\_\_dict__[key] = value**를 사용한다.
- set에서 setattr(instance, key, value)를 사용하면 \_\_set\_\_ 메서드가 호출되어 무한 루프에 빠진다.


```python
class Validation:

    def __init__(self, validation_function, error_msg):
        self.validation_function = validation_function
        self.error_msg = error_msg

    def __call__(self, value):
        if not self.validation_function(value):
            raise ValueError("{} {}".format(value, self.error_msg))

class Field(object):

    def __init__(self, name, *validations):
        self._name = name
        self.validations = validations
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self._name)

    def validate(self, value):
        for validation in self.validations:
            validation(value)

    def __set__(self, instance, value):
        print('set')
        self.validate(value)
        instance.__dict__[self._name] = value

class ClientClass(object):
    descriptor = Field(
        'descriptor',
        Validation(lambda x: isinstance(x, (int, float)), 'is not int or float'),
        Validation(lambda x: x>=0, 'is negative'),
    )
    def __init__(self):
        pass

client = ClientClass()
print(client.descriptor) #None
client.descriptor = 42 #set
print(client.descriptor) #42
client.descriptor = -42 #set
print(client.descriptor) #ValueError: -42 is negative

```

## __delete\_\_

- __get__과 __set__만큼 사용되지는 않음

```python
class ProtectedAttribute(object):
    def __init__(self, name):
        self._name = name
        
    def __set__(self, user, value):
        if value is None:
            raise ValueError("{name} property can't be None".format(name=self._name))
        user.__dict__[self._name] = value
    
    def __delete__(self, user):
        print('delete')
        user.__dict__[self._name] = None
    
class User(object):
    email = ProtectedAttribute("email")
    
    def __init__(self, username, email):
        self.username = username
        self.email = email
        
    def __str__(self):
        return self.username
    
user = User("user", "user@gmail.com")
print(user.email) #user@gmail.com
del user.email #delete
print(user.email is None) #True
user.email = None #email property can't be None

```

## __set_name\_\_

- 파이썬 3.6부터 만들어진 메서드
- 디스크립터 객체가 할당되는 속성의 이름이 인자로 넘겨진다

```python
class DescriptorWithName:
    def __init__(self, name=None):
        self._name = name
    
    def __set_name__(self, owner, name):
        self._name = name
    
    def __get__(self, instance, owner):
        return self._name
    
class ClientClass:
    descriptor = DescriptorWithName() #descriptor._name = 'descriptor'

client = ClientClass()
print(client.descriptor) #descriptor
```

## 디스크립터 유형

### 비데이터(non-data) 디스크립터

- __get\_\_ 메서드만 구현한 디스크립터
- 객체의 사전에 디스크립터와 동일한 이름의 키가 있으면 객체의 사전 값이 우선 적용됨

```python
class NonDataDescriptor:
    def __get__(self, instance, owner):
        return 100

class ClientClass:
    non_data_descriptor = NonDataDescriptor()

client = ClientClass()
print(client.non_data_descriptor) #100

client.non_data_descriptor = 200
print(client.non_data_descriptor) #200

del client.non_data_descriptor
print(client.non_data_descriptor) #100
```

### 데이터 디스크립터

- __set\_\_이나 \_\_delete\_\_ 메서드를 구현한 디스크립터
- 객체의 사전에 디스크립터와 동일한 이름을 갖는 키가 있더라도, 디스크립터 자체가 항상 먼저 호출됨
- == 객체의 키 값은 결코 사용되지 않음

```python
class DataDescriptor:
    
    def __init__(self):
        self._name = None
        
    def __get__(self, instance, owner):
        return 100

    def __set__(self, instance, value):
        instance.__dict__[self._name] = value
    
    def __set_name__(self, owner, name):
        self._name = name
        
    
class ClientClass:
    data_descriptor = DataDescriptor()

client = ClientClass()
print(client.data_descriptor) #100
print(vars(client)) #{}

client.data_descriptor = 200
print(vars(client)) #{'data_descriptor': 200}
print(client.data_descriptor) #100 => 객체의 사전에 접근하지 않고, 디스크립터가 먼저 호출됨

del client.data_descriptor #AttributeError: __delete__ => 디스크립터에 __delete__가 정의되어있지 않음

```

## 예시

```python
class RecordPlaceClass():
    def __init__(self, record_name):
        self._record_name = record_name
        self._name = None
    
    def __set_name__(self, owner, name):
        self._name = name
        
    def __get__(self, instance, owner_class):
        if instance is None:
            return None
        return instance.__dict__[self._name]
    
    def __set__(self, instance, place):
        self._record_place(instance, place)
        instance.__dict__[self._name] = place
        
    def _record_place(self, instance, place):
        self._set_default(instance)
        if(self._need_to_update_record(instance, place)):
            instance.__dict__[self._record_name].append(place)
    
    def _set_default(self, instance):
        instance.__dict__.setdefault(self._record_name, [])
    
    def _need_to_update_record(self, instance, place):
        current_place = instance.__dict__.get(self._name)
        return current_place != place
        

class TourClass():
    place = RecordPlaceClass('places_visited')

tour = TourClass()
tour.place = 'Seoul'
tour.place = 'Busan'
tour.place = 'Daegu'
tour.place = 'Daegu'
print(tour.place)
print(tour.places_visited)

```

## 파이썬 내부에서의 디스크립터 활용

### 함수와 메서드

- 메서드: 클래스 안에 정의된 객체에 바인딩 되는 함수
- **단지 인스턴스를 첫 번째 파라미터로 받는 함수일 뿐임**

```python
class MyClass:
    def method(self):
        self.x = 1
```

위 코드는 아래와 동일하다

```python
class MyClass: pass
def method(myclass_instance):
    myclass_instance.x = 1

method(MyClass())
```

```python
instance = MyClass()
instance.method()
```

파이썬은 위 코드를 실제로 아래처럼 처리한다

```python
instance = MyClass()
MyClass.method(instance)
```

- 이것은 파이썬이 디스크립터의 도움을 받아 내부적으로 처리되는 구문 변환이다.
- 함수는 디스크립터 프로토콜로 구현되어, instance.method() 호출시
- instance.method 부분이 먼저 평가 되고, method.__get\_\_() 메서드가 먼저 호출된다.
- __get\_\_ 메서드는 함수를 메서드로 변환한다.
- 즉, 함수를 작업하려는 객체의 인스턴스에 바인딩 한다.

예시:
```python
from types import MethodType

class Method:
    def __init__(self, name):
        self._name = name
        
    def __call__(self, instance, arg1, arg2):
       print(f"{self._name}: {instance} 호출됨. 인자는 {arg1}, {arg2}") 

class MyClass:
    method = Method("MyClassMethod")

instance = MyClass()
method = Method("taehun")
method(instance, 1, 2)

MyClass.method(instance, 1, 2)
instance.method(instance, 1, 2) #instance를 따로 넘겨주는 구현이 없기 때문에, instance를 넘겨주지 않으면 오류 발생

instance.method = MethodType(instance.method, instance)
instance.method(1,2) #method를 instance에 바인딩하여 method의 인자로 instance가 넘어가게 함


def __get__(self, instance, owner):
    if instance is None:
        return self
    return MethodType(self, instance)

setattr(Method, '__get__', __get__) #Method class에 __get__ 구현하여 method 호출시 instance에 바인딩

instance = MyClass()
instance.method(1,2)
```

### 메서드를 위한 빌트인 데코레이터

- @property, @classmethod, @staticmethod 데코레이터는 모두 디스크립터이다.
- @classmethod를 사용하면 디스크립터의 __get\_\_ 함수는 데코레이팅 함수에 첫 번째 파라미터로 메서드를 소유한 클래스를 넘겨준다.
- @staticmethod를 사용하면 __get\_\_ 함수는 함수의 첫 번째 파라미터에 self를 바인딩하는 작업을 취소한다.

### 슬롯(Slot)

- 클래스에 \_\_slot__ 속성을 정의하면 클래스가 기대하는 특정 속성만 정의하고 다른 것은 제한할 수 있다.
- 이 속성을 정의하면 클래스는 정적이 되고 \_\_dict__ 속성을 갖지 않는다.
- 객체의 사전이 없는데 어떻게 속성을 가져올 수 있을까?
  - \_\_slot__에 정의된 이름마다 디스크립터를 만들어서 값을 저장!
