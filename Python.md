# Decorator

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
```


