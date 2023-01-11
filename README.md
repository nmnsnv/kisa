
# Kisa - Python Object Oriented System

Kisa is an advanced, comprehensive Object Oriented System written for Python.

Kisa takes on itself many of the repetitive, unnecessary code sections and provides them automatically, such as:

* Auto generated:
    * Getters (See [Private/Public Attributes](#private_public_attributes))
    * Setters (See [Private/Public Attributes](#private_public_attributes))
    * Constructor (See [Constructor](#constructor))
* A better inheritance system (including abstract, interfaces. See [Inheritance](#inheritance))
* Lazy attributes (See [Lazy Attributes](#lazy_attributes))
* Enforcement of:
    * Attribute type - Including [*Recursive Types* **BETA**](#recursive_types) (types as strings)
    * Inheritance:
        * Abstract class/interface cannot be created
        * Abstract methods implemented
    * Existance of attributes
* Attribute modifiers (before/around/after) available for every:
    * Attribute
    * Method
    * Some of Python native methods, such as:
        * `__init__` (See [Python special methods](#python_special_methods))
        * `__new__` (See [Python special methods](#python_special_methods))
    * Static methods (See [Static Methods](#kisa_static_methods))
    * Static attributes (See [`kisa.StaticInfo`](#kisa_static_info))

Kisa is designed to make classes in Python faster to write, maintain, better organized, and safer.

# Create class:

The only thing required in order to create Kisa class is to pass the `metaclass=kisa.Class` argument at class creation

```python
import kisa

class EmptyClass(metaclass=kisa.Class):
    pass
```

# Class Attributes:

In Kisa, unlike Python native OOP, attributes are defined at class decleration and not during runtime. This cannot be modified.

Kisa has 2 type of attributes:

* kisa.Info - Describes regular attributes. See [`kisa.Info`](#kisa_info)
* kisa.StaticInfo - Describes static attributes. See [`kisa.StaticInfo`](#kisa_static_info)

Kisa attribute decleration is as follows:

```python
class Person(metaclass=kisa.Class):
    amount_created = kisa.StaticInfo(final=False, type=int, default=0)

    firstname = kisa.Info(final=False, type=str, required=True)
    lastname = kisa.Info(final=False, type=str, required=True)
    birth_country = kisa.Info(final=True, type=str, required=True)

    # Otherwise all objects would share the same list
    friends = kisa.Info(final=True, type=list, required=False, default=lambda: [])

    age = kisa.Info(final=False, type=int, required=True, allow_none=False)
```

## <a id="kisa_info"></a> kisa.Info:

`kisa.Info` Class is used to define attribute parameters:

* `final` - Is variable final, i.e. cannot be modified. (default `False`)
* `type` - Type of the attribute (default `object`). For recursive type (class A has type of class A) see [Recursive Types **BETA**](#recursive_types)
* `required` - Is attribute required to be passed to constructor. (default `True`)
* `default` - Default value - Note that if value is `callable` (i.e. a function/lambda) the default value will be the return value of the function (default `None`). See [`default`](#default)
* `allow_none` - Could the attribute be None (default `True`) - If `False`, it will raise Exception when trying to set the attribute value to `None`
* `lazy` - Is attribute is lazy (default `False`) - If `True`, its value will be assigned only when it's value is required (See [Lazy Attributes](#lazy_attributes))

## <a id="default"></a> default

When declaring new attribute in Kisa, we pass the `deafult` attribute to default the attribute value to anything we'd like. It can be:

* Primitive (e.g. `string` or `int`)
* Reference (e.g. `list`, `dict` or some object) **This option is highly discouraged! use [lambda expression](#default_lambda_expression) instead**
    * NOTE: if you'll pass a reference, it will be shared with all of the class objects.
* Lambda expression - See [`default` lambda expression](#default_lambda_expression)

## <a id="default_lambda_expression"></a> argument ```default``` - lambda expression

Kisa automatically detects `callabale` objects (i.e. method/lambda),
calls them and the attribute value to the returned value.

```python
class SchoolClass(metaclass=kisa.Class):
    # NOTE: If we didnt use lambda, all objects would point to the same list
    student_list = kisa.Info(default=lambda: [])
```

Say we want to default to a method rather then a lambda (perhaps since we require more complicated initialization process).
It can be problematic to reference to a method since the method will only be declared later.

For instance, the following will **NOT** work:

```python
# This will NOT work
class Logger(metaclass=kisa.Class):
    # Will raise Exception stating "init_log_file" does not exist
    log_file = kisa.Info(default=init_log_file)

    def init_log_file(self):
        file_path="/var/log/my_logger.log"
        if not self.file_exists(file_path):
            self.create_file(file_path)
        return self.open_file(file_path, mode="w")

    # Rest of the code
    # ...
```

Kisa can pass to default methods either 0 or 1 parameters, depends on what the method expects to receive:
* 0 paramters - Kisa will pass no parameters to the method
* 1 parameters - Kisa will pass the self object to the method

Given that. We can accomplish multi-line initialization by using lambda with self parameter, and from there calling the initialization method

Example:

```python
# This will work
class Logger(metaclass=kisa.Class):
    # 0 parameters
    debug_level = kisa.Info(default = lambda: "production")

    # 1 parameters
    log_file = kisa.Info(default=lambda self: self.init_log_file())

    def init_log_file(self):
        file_path="/var/log/my_logger.log"
        if not self.file_exists(file_path):
            self.create_file(file_path)
        return self.open_file(file_path, mode="w")

    # Rest of the code
    # ...
```

# <a id="attributes_assignment_order"></a> Attributes Assignment Order

Another thing that might prove useful, is using an attribute value during another attribute default initialization. Kisa can handle those requests and will handle those requests and will assign attributes values in the order they are required by the default values

Example:

```python
class A(metaclass=kisa.Class):
    a = kisa.Info(final=True,  default=lambda self: self.b() + self.d() + 1)
    b = kisa.Info(final=True,  default=lambda self: self.c() + 1)
    c = kisa.Info(final=True,  default=0)
    d = kisa.Info(final=False, required=True)

a=A(d=3)
print(a.a()) # prints 5
print(a.b()) # prints 1
print(a.c()) # prints 0
```

In this example, the execution order is as follows:

1. `d` is assigned - User provided values are always assigned first.
2. `c` is assigned - Required by `b`.
3. `b` is assigned - Required by `a`.
4. `a` is assigned - Nobody requires it.

If we'll take a look at the logger we've shown before, it will prove useful:

```python
class Logger(metaclass=kisa.Class):
    debug_level = kisa.Info(type=str, default="production")
    file_path = kisa.Info(type=str, default="/var/log/my_logger.log")

    log_file = kisa.Info(default=lambda self: self.init_log_file())

    def init_log_file(self):
        if not self.file_exists(file_path.file_path()):
            self.create_file(file_path.file_path())
        self.write_log("Initialized Log File")
        return self.open_file(file_path.file_path(), mode="w")

    def write_log(self, msg_log_level, msg):
        if msg_log_level == self.debug_level():
            print(msg)

    # Rest of the code
    # ...
```

The example would first create `file_path`, then `debug_level` and only then it will complete `log_file`. This example is safe to use and the assignment order is enforced

## Static Info - `kisa.StaticInfo`

See [Static Attributes - kisa.StaticInfo](#kisa_static_info)

## <a id="lazy_attributes"></a> Lazy Attributes

A lazy attribute is an attribute which his value is retreived only when required and not at construction. One instance when this is useful is when an attribute usage is questionable, but also expensive to retrieve, so we'll avoid it until we must get it.

Lazy attribute works exactly like regular attribute, but its value will be calculated when:

* Using the attribute getter for the first time - Its value will be the value retrieved from `default`.
* Its value was given from the constructor - In this case, the default value will NOT be calculated.
* Its value was given from the setter - In this case, the default value will NOT be calculated.

Examples:

```python
class DataProcessor(metaclass=kisa.Class):
    file_name      = kisa.Info(type=str, allow_none=False, required=True)
    processed_data = kisa.Info(type=str, allow_none=False, default="get_data", lazy=True)

    def get_data(self):
        print(f"Getting data for {self.file_name()}")
        with open(self.file_name()) as f:
            data = f.read()

        # do some processing on the data
        # ...

        return processed_data

    def post_data(self, data):
        # Post the data online
        # ...

# NOTE: This file is very very large! (1~2gb)
data_processor = DataProcessor(file_name="/var/log/app.log")

# do some actions...

# Only now it will get processed_data value and would print its log
post_data(data_processor.processed_data())
```

# <a id="constructor"></a> Constructor:

Kisa automatically generates the constructor by itself:

```python
class Person(metaclass=kisa.Class):
    firstname = kisa.Info(final=False, type=str, required=True)
    lastname = kisa.Info(final=False, type=str, required=True)
    favorite_food = kisa.Info(final=False, type=str, required=True)
    friends = kisa.Info(final=True, type=int, required=False, default=lambda: [])

# NOTE: friends is generated automatically
myself = Person(firstname="Noam", lastname="Nis", favorite_food="Pizza")
```

* Note: It is possible to modify the construction process, as explained in the [Overriding constructor](#overriding_constructor) section

# <a id="recursive_types"></a> Recursive Types - **BETA**

**IMPORTANT** - Recursive Types is in **beta** and might not detect the classes.

A common practice when writing classes is to use recursive types, i.e. having classes requiring themselves (class `A` has attribute of type `A`).
Another issue that might arise is the usage of a class that will only be declared later in the file.

Example (The following code will not work):

```python
# Example 1 - Will not work
class A(metaclass=kisa.Class):
    a = kisa.Info(type=A)
```

```python
# Example 2 - Will not work
class A(metaclass=kisa.Class):
    b = kisa.Info(type=B)

class B(metaclass=kisa.Class):
    a = kisa.Info(type=A)
```

```python
# Example 3 - Will not work (class B doesn't exist at time of creating class A)
class A(metaclass=kisa.Class):
    b = kisa.Info(type=B)

class B(metaclass=kisa.Class):
    pass
```

In order to solve this issue, Kisa supports to pass types by string and not by reference.

Kisa is designed to handle:

* local package type
* other package type

A couple examples:

```python
# Example 1
class A(metaclass=kisa.Class):
    a = kisa.Info(type="A")
```

```python
# Example 2
class A(metaclass=kisa.Class):
    b = kisa.Info(type="B")

class B(metaclass=kisa.Class):
    a = kisa.Info(type=A)
```

```python
# Example 3
class A(metaclass=kisa.Class):
    b = kisa.Info(type="B")

class B(metaclass=kisa.Class):
    pass
```

This will also work:

```python
class Person(metaclass=kisa.Class):
    fullname = kisa.Info(type="str", required=True)
    age = kisa.Info(type="int", required=True)
```

**NOTE** - When passing type as a string, the type validation will only occur when trying to create the first instance, not before

# <a id="private_public_attributes"></a> Private/Public Attributes:

In Kisa, all attributes are Private and can only be accessed via Get/Set method.
Those methods are generated automatically, and can be modified.
This is explained with greater detail in the [Custom getter/setter](#custom_getter_setter) section.

## getter/setter:

* NOTE: setter also returns the value it has set

Use as follows:
```python
myself = Person(firstname="Noam", lastname="Nis", favorite_food="Pizza")

myself.firstname() # Getter (returns "Noam")
myself.favorite_food("Burger") # Setter (returns "Burger")

```

Please note that the get/set methods are actually the same method but passed with different number of parameters:

* When called with 1 parameter - it would be treated as a setter method.
* When called with no parameters - it will be treated as a getter method.

## <a id="custom_getter_setter"></a>Custom getter/setter:

We can also override Kisa default getter/setter by using the decorator

* `@kisa.getter('attribute_name')` - expects to decorate a function that receives `self` and the attribute value
```python
class Person(metaclass=kisa.Class):
    firstname = kisa.Info(final=False, type=str, required=True)

    @kisa.getter('firstname')
    def get_firstname(self, firstname_value):
        return f"Mr. {firstname_value}"

noam_person = Person(firstname="Noam")
dani_person = Person(firstname="Dani")

print(noam_person.firstname()) # prints "Mr Noam"
print(dani_person.firstname()) # prints "Mr Dani"
```

* `@kisa.setter(attribute_name)` - expects to decorate a function that receives `self` and the new value to be set
    * Note: The value that is set to the attribute at the end is the value that is returned

```python
class Employee(metaclass=kisa.Class):
    salary = kisa.Info(final=False, type=str, required=True)

    @kisa.setter('salary')
    def set_salary(self, new_salary):
        if new_salary <= 0:
            raise Exception("Salary must be bigger then 0!")
        return new_salary

noam = Employee(salary=15)

noam.salary(-30) # Raises exception: Salary must be bigger then 0!
```

# <a id="attribute_modifier"></a>Attribute Modifier:

Attribute Modifier is a way to redirect an attribute/function call and maniputlate it, Kisa has 3 Attribute Modifiers:

* before - Called before every call to the attribute/function
    * Receives:
        * self
        * attribute name
        * `*args`
        * `**kwargs`
* around - Called to surround every call to the attribute/function, and can decide if it wants to call the function at all and with what parameters (see [Around Modifier](#around_modifier))
    * Receives:
        * self
        * attribute name
        * next call - Receives
        * `*args`
        * `**kwargs`
* after - Called after every call to the function
    * Receives:
        * self
        * attribute name
        * `*args`
        * `**kwargs`

## <a id="around_modifier"></a> Around Modifier

Around Modifier allows us to manipulate the method call:
* Decide what args goes to the original method - The args passes to `next_call` method
* What value the original method will finally return - The value returned from the `around` method

## Call Order:

1. all before methods, same order in code
2. all around methods, same order in code (this includes the method call itself)
3. all after methods, same order in code

## Example:

```python
class Sound(metaclass=kisa.Class):
    # ...

    def play(self, filename):
        # plays a sound from file
        pass

    @kisa.before("play", "play_reverse")
    def play_intro_sound(self, attr_name, filename):
        # plays intro sound before every sound play
        pass

    @kisa.around("play", "play_reverse")
    def validate_sound_exists(self, attr_name, next_call, filename):
        # if file exists, play normally, otherwise play an error sound
        if self.file_exists(filename):
            return next_call(filename)
        else:
            return next_call("error_sound.mp3")

    @kisa.after("play", "play_reverse")
    def play_exit_sound(self, attr_name, filename):
        # plays exit sound after every sound play
        pass
```

**NOTE:** the attribute modifier itself, which is a function won't exist in the class/objects

```python
class ModifierClass(metaclass=kisa.Class):
    def foo(self):
        pass

    @kisa.before("foo")
    def bar(self):
        pass

obj = ModifierClass()
obj.bar() # Throws exception, bar doesn't exist
```

## Modifying multiple attributes at once

We can pass before/around/after a list of attributes, kisa will hook to all of the attributes in the list

## Example:

The following example shows part of a logger system that creates a log file for each log level

```python
import os

class Logger(metaclass=kisa.Class):
    info_file  = kisa.Info(type=str, required=True, allow_none=False, final=False)
    warn_file  = kisa.Info(type=str, required=True, allow_none=False, final=False)
    error_file = kisa.Info(type=str, required=True, allow_none=False, final=False)

    @kisa.before("info_file", "warn_file", "error_file")
    def create_if_not_exists(self, attr_name, *args):
        if len(args) == 0:
            # Getter, skip
            return
        else:
            # Setter
            file_name = args[0]
            if not os.path.exists(file_name):
                # Create file
                open(file_name, "w").close()

# Creates 3 files: ./info.txt ./warn.txt ./error.txt
logger = Logger(info_file="./info.txt", warn_file="./warn.txt", error_files="./error.txt")
```

## <a id="python_special_methods"></a> Python special methods (`__init__`, `__setattr__`, `__getattribute__`, `__call__`, etc...)

Kisa supports Attribute Modifiers for Python native methods. Currently supports:

* `__init__`: Allows you to modify the constructor, or run your own things - see [Overriding constructor](#overriding_constructor) for more details
* `__new__`: Allows you to modify the `__new__` call during object creation, in order to modify it (See [Singleton](#singleton) for example)

# Static attributes/methods

## <a id="kisa_static_info"></a> Static Attributes - `kisa.StaticInfo`

In order to declare static attributes we use `kisa.StaticInfo`. `kisa.StaticInfo` behaves exactly like [Regular Attributes (`kisa.Info`)](#kisa_info) except for 2 differences:
* `required` - is **NOT** available for static attributes. This is so since static attributes are not constructed.
* `default` - lambda **can get only 0** attributes.

Example:

```python
class Male(metaclass=kisa.Class):
    nickname = kisa.StaticInfo(final=True, type=str, default=lambda: "Mr.")

print(Male.nickname()) # prints "Mr."

male_obj = Male()

print(male_obj.nickname()) # prints "Mr."

male_obj.nickname("Sir") # We can modify static attributes from instances

print(male_obj.nickname()) # prints "Sir"
print(Male.nickname()) # prints "Sir"
```

## <a id="kisa_static_methods"></a> Static Methods - `@kisa.static`

In order to define static methods, simply use the `@kisa.static` decorator and Kisa will create a static method itself

Example:

```python
class Math(metaclass=kisa.Class):
    @kisa.static
    def add(a, b):
        return a + b

print(Math.add(1, 2)) # prints 3

my_math = Math()
print(my_math.add(1, 2)) # prints 3
```

## Static **Modifiers**

Static Modifiers, work exactly as regular [Attribute Modifiers](#attribute_modifier).
Static Modifiers are automatically detected and act as static methods themselves

Example:

```python
class Math(metaclass=kisa.Class):
    @kisa.static
    def add(a, b):
        return a + b

    @kisa.before("add")
    def before_add(a, b):
        print("Calling a+b")

class Person(metaclass=kisa.Class):
    amount_created = kisa.StaticInfo(final=True, type=int, default=lambda: 0)

    @kisa.before("amount_created")
    def before_amount_changed(new_val=None):
        print(f"New val = {new_val}")

Person.amount_created(1)
```

## <a id="singleton"></a> Singleton

We can use `StaticInfo` in order to create Singleton:

```python
class Logger(metaclass=kisa.Class):
    _initialized = kisa.StaticInfo(type=bool, default=False, allow_none=False)
    # NOTE: Why we use lazy is explained after the example
    _singleton = kisa.StaticInfo(type="Logger", lazy=True)

    name=kisa.Info(type=str)

    @kisa.around('__new__')
    def get_singleton(cls, attr_name, next_call, *args, **kwargs):
        if Logger._singleton() is None:
            Logger._singleton(next_call(*args, **kwargs))
        return Logger._singleton()

    @kisa.around('__init__')
    def init(self, attr_name, next_call, *args, **kwargs):
        if self._initialized() is None:
            next_call(*args, **kwargs)
            self._initialized(True)


l1 = Logger(name="NoamLogger")
l2 = Logger()

print(l1 == l2) # Prints "True"
```

Why `_singleton` is `lazy`?

The reason lies in the fact that static attributes values are computed during class creation.
That means that by that time there is no `Logger` class to be found.
When `_singleton` is `lazy`, kisa will look for type `Logger` only when we'll assign a value to it.
By that time `Logger` will already be defined.

# <a id="inheritance"></a> Inheritance:

Inheritance works the same as in python OOP:

```python
class Vehicle(metaclass=kisa.Class):
    wheels_amount = kisa.Info(type=int, final=True)

    def drive(self, dest):
        print(f"Driving to: {dest} with {self.wheels_amount()} wheels")

class Car(metaclass=kisa.Class, extends=Vehicle):
    def drive(self):
        print("A car driving...")
        self._super().wheels_amount()
```

**NOTE:**

* the native `super()``` method does not work in Kisa, use instead ```self._super()` instead
* Kisa does not support Python native inheritance, only 1 inheritance of class is allowed, via `extends=<extended_class>` as seen in the example

# Abstract Class

Kisa supports abstract classes

```python
class Shape(metaclass=kisa.AbstractClass):
    @kisa.abstract
    def get_circumference(self):
        pass


class Quadrangle(metaclass=kisa.AbstractClass, extends=Shape):
    a = kisa.Info(type=int, required=True)
    b = kisa.Info(type=int, required=True)
    c = kisa.Info(type=int, required=True)
    d = kisa.Info(type=int, required=True)

    def get_circumference(self):
        return self.a() + self.b() + self.c() + self.d()


class Rectangle(metaclass=kisa.Class, extends=Quadrangle):
    pass

```

# Interface

Kisa supports interfaces

* There can be multiple interfaces in a single class/interface
* Interface can only contain `@kisa.abstract` methods (no attributes/implementations)

```python
class Savable(metaclass=kisa.Interface):
    @kisa.abstract
    def save():
        pass

class Loadable(metaclass=kisa.Interface):
    @kisa.abstract
    def load():
        pass

# A safe class is a class that can be saved/loaded to/from hard disk
class ISafeClass(metaclass=kisa.Interface, implements=[Savable, Loadable]):
    pass

class ModifiableConfiguration(metaclass=kisa.Class, implements=ISafeClass):
    def save(self, path):
        # TODO: Save to path
        pass

    def load(self, path):
        # TODO: Load object from path
        pass
```

* Note: For single implemented interface, it is not required to be passed as list
* Note: Kisa currently does not support method signature enforcement

## <a id="overriding_constructor"></a> Overriding constructor

* **NOTE:** Even though the following example uses inheritance, you are by no means required to use inheritance in order to override the constructor

Say we want Rectangle to receive only arguments `a` and `b`, and set the arguments `c` and `d` to equal `a` and `b` accordingly. we can achieve this by applying `kisa.around` to `__init__` constructor.

This in turn will enable you to intercept the call to the constructor before it is called, make your own changes and then let the process proceed normally.

```python
class Shape(metaclass=kisa.AbstractClass):
    @kisa.abstract
    def get_circumference(self):
        pass

class Quadrangle(metaclass=kisa.AbstractClass, extends=Shape):
    a = kisa.Info(type=int, required=True)
    b = kisa.Info(type=int, required=True)
    c = kisa.Info(type=int, required=True)
    d = kisa.Info(type=int, required=True)

    def get_circumference(self):
        return self.a() + self.b() + self.c() + self.d()

class Rectangle(metaclass=kisa.Class, extends=Quadrangle):
    @kisa.around("__init__")
    def around_init(self, attr_name, next_call, a: int, b: int):
        # NOTE: Since Python __init__ doesn't return anything,
        #       we are not required to return the value of next(...)
        next_call(a=a, b=b, c=a, d=b) # Calls Kisa internal constructor

# r = Rectangle(a=1, b=2, c=3, d=4) - Throws Exception, expects only params 'a' and 'b'
r = Rectangle(a=1, b=2) # a=1, b=2, c=1, d=2
```

# A full example:

```python

import kisa

class Savable(metaclass=kisa.Interface):
    @kisa.abstract
    def save():
        pass

class Loadable(metaclass=kisa.Interface):
    @kisa.abstract
    def load():
        pass

# A safe class is a class that can be saved/loaded to/from hard disk
class ISafeClass(metaclass=kisa.Interface, implements=[Savable, Loadable]):
    pass

class Shape(metaclass=kisa.AbstractClass, implements=ISafeClass):
    @kisa.abstract
    def get_circumference():
        pass

    @kisa.abstract
    def get_area():
        pass

    def load(self):
        print("Loading...")
        print("Loaded successfully")

    def save(self):
        print("Saving...")
        print("Saved successfully")


class Quadrangle(metaclass=kisa.AbstractClass, extends=Shape):
    a = kisa.Info(type=int, required=True)
    b = kisa.Info(type=int, required=True)
    c = kisa.Info(type=int, required=True)
    d = kisa.Info(type=int, required=True)

    def get_circumference(self):
        return self.a() + self.b() + self.c() + self.d()


class Rectangle(metaclass=kisa.Class, extends=Quadrangle):

    @kisa.around("__init__")
    def around_init(self, attr_name, next_call, a: int, b: int):
        next_call(a=a, b=b, c=a, d=b)

    def get_self(self):
        return f"{self.a()}x{self.b()}"

    def get_area(self):
        return self.a() * self.b()

    def describe(self, desc):
        return f">> {desc}"


r = Rectangle(a=3, b=2)

# Prints 10
print(r.get_circumference())

# Prints 6
print(r.get_area())

# Prints Saving...
#        Saved successfully
r.save()

# Prints Loading...
#        Loaded successfully
r.load()
```

# Author

Noam Nisanov - `noam.nisanov@gmail.com`
