import asyncio

class SingletonOnArgs(type):
    _instances = {}

    # async def __call__(cls, *args, **kwargs):
    #     # Create a key based on the class and initialization arguments
    #     key = (cls, args, tuple(sorted(kwargs.items())))
        
    #     # Check if an instance with these arguments already exists
    #     if key not in cls._instances:
    #         # If not, create and store the instance
    #         if asyncio.iscoroutinefunction(super().__call__):
    #             cls._instances[key] = await super().__call__(*args, **kwargs)
    #         else:
    #             cls._instances[key] = super().__call__(*args, **kwargs)
    #     # Return the instance (new or existing)
    #     return cls._instances[key]
