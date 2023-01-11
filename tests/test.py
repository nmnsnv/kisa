
import unittest
import kisa


class KisaUnitTests(unittest.TestCase):

    def test_empty_class(self):
        class EmptyClass(metaclass=kisa.Class):
            pass

        EmptyClass()

    def test_non_final(self):
        class Person(metaclass=kisa.Class):
            name = kisa.Info(type=str, required=True, final=False)

        p = Person(name="Noam")
        self.assertEqual(p.name(), "Noam")

        self.assertEqual(p.name("Nisanov"), "Nisanov")
        self.assertEqual(p.name(), "Nisanov")

    def test_static_attribute_non_final_state(self):
        class ClassFinalStatic(metaclass=kisa.Class):
            nickname = kisa.StaticInfo(final=False, type=str, default="A")

        self.assertEqual(ClassFinalStatic.nickname(), "A")
        self.assertEqual(ClassFinalStatic.nickname("B"), "B")
        self.assertEqual(ClassFinalStatic.nickname(), "B")

        obj = ClassFinalStatic()

        self.assertEqual(obj.nickname(), "B")
        self.assertEqual(obj.nickname("C"), "C")
        self.assertEqual(obj.nickname(), "C")

    def test_final(self):
        class Person(metaclass=kisa.Class):
            name = kisa.Info(type=str, required=True, final=True)

        p = Person(name="Noam")
        try:
            p.name("Nisanov")
        except Exception as e:
            return
        self.fail("Can't modify final attribute")

    def test_static_attribute_final_state(self):
        class ClassFinalStatic(metaclass=kisa.Class):
            nickname = kisa.StaticInfo(final=True, type=str, default="A")

        obj = ClassFinalStatic()

        self.assertEqual(ClassFinalStatic.nickname(), "A")
        self.assertEqual(obj.nickname(), "A")
        try:
            ClassFinalStatic.nickname("B")
            self.fail("Final attribute was modified")
        except AssertionError:
            raise
        except:
            pass
        try:
            obj.nickname("C")
            self.fail("Final attribute was modified")
        except AssertionError:
            raise
        except:
            pass

    def test_default_value(self):
        class Person(metaclass=kisa.Class):
            name = kisa.Info(type=str, default="Noam")
        p = Person()
        self.assertEqual(p.name(), "Noam")

    def test_default_value_lambda(self):
        class Person(metaclass=kisa.Class):
            name = kisa.Info(type=str, default=lambda: "Noam")
        p = Person()
        self.assertEqual(p.name(), "Noam")

    def test_default_value_method(self):
        class Person(metaclass=kisa.Class):
            name = kisa.Info(type=str, default=lambda self: self.gen_name())

            def gen_name(self):
                return "Noam"

        p = Person()
        self.assertEqual(p.name(), "Noam")

    def test_setter(self):
        class Person(metaclass=kisa.Class):
            name = kisa.Info(type=str, default="Noam")

            @kisa.setter("name")
            def set_name(self, val):
                return f"Mr {val}"

        p1 = Person()
        p2 = Person(name="Nisanov")
        self.assertEqual(p1.name(), "Mr Noam")
        self.assertEqual(p2.name(), "Mr Nisanov")

    def test_setter_static(self):
        class SetterClassStatic(metaclass=kisa.Class):
            value = kisa.StaticInfo(type=str, default="X")

            @kisa.setter("value")
            def set_value(val):
                return f"->{val}"

        self.assertEqual(SetterClassStatic.value(), "->X")
        self.assertEqual(SetterClassStatic.value("Y"), "->Y")
        self.assertEqual(SetterClassStatic.value(), "->Y")

    def test_getter(self):
        class Person(metaclass=kisa.Class):
            name = kisa.Info(type=str, default="Noam")

            @kisa.getter("name")
            def get_name(self, val):
                return f"Mr {val}"

        p1 = Person()
        p2 = Person(name="Nisanov")
        self.assertEqual(p1.name(), "Mr Noam")
        self.assertEqual(p2.name(), "Mr Nisanov")

    def test_getter_static(self):
        class GetterClassStatic(metaclass=kisa.Class):
            value = kisa.StaticInfo(type=str, default="X")

            @kisa.getter("value")
            def get_value(val):
                return f"->{val}"

        self.assertEqual(GetterClassStatic.value(), "->X")
        self.assertEqual(GetterClassStatic.value("Y"), "Y")
        self.assertEqual(GetterClassStatic.value(), "->Y")

    def test_abstract(self):
        class Shape(metaclass=kisa.AbstractClass):
            @kisa.abstract
            def get_circumference(self):
                pass

        class Quadrangle(metaclass=kisa.Class, extends=Shape):
            a = kisa.Info(type=int, required=True)
            b = kisa.Info(type=int, required=True)
            c = kisa.Info(type=int, required=True)
            d = kisa.Info(type=int, required=True)

            def get_circumference(self):
                return self.a() + self.b() + self.c() + self.d()

        shape = None
        try:
            shape = Shape()
        except:
            pass

        self.assertEqual(shape, None, "Abstract class instance is not allowed")

        quad = Quadrangle(a=1, b=2, c=3, d=4)

        self.assertEqual(quad.get_circumference(), 10)

    def test_inheritance_attributes(self):
        class Vehicle(metaclass=kisa.Class):
            wheels_amount = kisa.Info(type=int, final=True)

        class Car(metaclass=kisa.Class, extends=Vehicle):
            pass
        car = Car(wheels_amount=4)
        self.assertEqual(car.wheels_amount(), 4)

    def test_override_constructor(self):
        class Vehicle(metaclass=kisa.Class):
            wheels_amount = kisa.Info(type=int, final=True)

        class Car(metaclass=kisa.Class, extends=Vehicle):
            @kisa.around("__init__")
            def constructor(obj_self, attr_name, next):
                self.assertEqual(attr_name, "__init__")
                next(wheels_amount=4)

        car = Car()
        self.assertEqual(car.wheels_amount(), 4)

    def test_interface(self):
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

        class SafeClass(metaclass=kisa.Class, implements=ISafeClass):

            def load(self):
                print("Loading...")
                print("Loaded successfully")

            def save(self):
                print("Saving...")
                print("Saved successfully")

        NotImplementedClass = None
        try:
            class NotImplementedClass(metaclass=kisa.Class, implements=ISafeClass):
                pass
        except Exception as e:
            pass

        self.assertEqual(NotImplementedClass,
                         None,
                         "Class did not implement interface methods and should throw exception")

        self.assertEqual(type(SafeClass()), SafeClass)

    def test_static_attribute_disallow_none(self):
        class ClassNonFinalStatic(metaclass=kisa.Class):
            nickname = kisa.StaticInfo(final=False,
                                       type=str,
                                       allow_none=False,
                                       default="Nis")

        self.assertEqual(ClassNonFinalStatic.nickname(), "Nis")

        ClassTypeNoneStatic = None
        try:
            class ClassTypeNoneStatic(metaclass=kisa.Class):
                nickname = kisa.StaticInfo(type=str, allow_none=False)
        except Exception as e:
            pass
        self.assertEqual(ClassTypeNoneStatic,
                         None,
                         "allow_none=False should not allow str type to be None")

    def test_allow_none(self):
        class Person(metaclass=kisa.Class):
            name = kisa.Info(type=str, required=False, allow_none=True)

        p = Person()
        self.assertEqual(p.name(), None)

        p.name("Noam")
        self.assertEqual(p.name(), "Noam")

    def test_static_allow_none(self):
        class ClassStatic(metaclass=kisa.Class):
            name_static = kisa.StaticInfo(type=str, allow_none=True)

        self.assertEqual(ClassStatic.name_static(), None)

        ClassStatic.name_static("Noam")
        self.assertEqual(ClassStatic.name_static(), "Noam")

    def test_recursive_type(self):
        class A(metaclass=kisa.Class):
            a = kisa.Info(type="A", required=False)

        _ = A(a=A(a=A()))

        # Example 2
        class A(metaclass=kisa.Class):
            b = kisa.Info(type="B")

        class B(metaclass=kisa.Class):
            a = kisa.Info(type=A, required=False)

        _ = A(b=B())

        # Example 3
        class A(metaclass=kisa.Class):
            b = kisa.Info(type="B")

        class B(metaclass=kisa.Class):
            name = kisa.Info(type=str)

        _ = A(b=B(name="Noam"))

    def test_before(self):
        for final_status in (True, False):
            class A(metaclass=kisa.Class):
                name = kisa.Info(type=str, default=lambda: "objName",
                                 final=final_status)

                @kisa.before("name")
                def before_name(self_obj, attr_name, *args):
                    self.assertEqual(attr_name, "name")

            a = A()
            self.assertEqual(a.name(), "objName")

    def test_before_static(self):
        for final_status in (True, False):
            class A(metaclass=kisa.Class):
                name = kisa.StaticInfo(type=str, default=lambda: "staticName",
                                       final=final_status)

                @kisa.before("name")
                def before_name(attr_name, *args):
                    self.assertEqual(attr_name, "name")

            self.assertEqual(A.name(), "staticName")

    def test_before_multiple_methods(self):
        class Person(metaclass=kisa.Class):
            firstname = kisa.Info(type=str, required=True)
            age = kisa.Info(type=int, required=True)

            @kisa.before("firstname", "age")
            def before(self_obj, attr, *args):
                self.assertFalse(attr not in ('firstname', 'age'),
                                 f"Attribute is unknown {attr}")

        p = Person(firstname="Noam", age=22)
        self.assertEqual(p.firstname(), "Noam")
        self.assertEqual(p.age(), 22)

    def test_before_multiple_methods_static(self):
        class StaticClass(metaclass=kisa.Class):
            arg1 = kisa.StaticInfo(type=str, default="StaticArg")
            arg2 = kisa.StaticInfo(type=int, default=13)

            @kisa.before("arg1", "arg2")
            def before(attr, *args):
                self.assertFalse(attr not in ('arg1', 'arg2'),
                                 f"Attribute is unknown {attr}")

        self.assertEqual(StaticClass.arg1(), "StaticArg")
        self.assertEqual(StaticClass.arg2(), 13)

    def test_around_multiple_methods(self):
        foo_called = False
        bar_called = False

        class MyClass(metaclass=kisa.Class):

            def foo(self, a, b):
                nonlocal foo_called
                foo_called = True
                return 1

            def bar(self, a):
                nonlocal bar_called
                bar_called = True
                return 2

            @kisa.around("foo", "bar")
            def around_tester(self_obj, method_name, next, *args):
                if method_name == "foo":
                    self.assertEqual(len(args), 2)
                    self.assertEqual(args[0], 1)
                    self.assertEqual(args[1], 'a')
                    return next(*args)
                elif method_name == "bar":
                    self.assertEqual(len(args), 1)
                    self.assertEqual(args[0], 'call')
                    return next(*args)
                else:
                    self.fail(f"Unknown method arround wraps: {method_name}")

        obj = MyClass()
        self.assertEqual(obj.foo(1, 'a'), 1)
        self.assertEqual(obj.bar('call'), 2)

        self.assertEqual(foo_called, True)
        self.assertEqual(bar_called, True)

    def test_around_multiple_methods_static(self):
        foo_called = False
        bar_called = False

        class StaticClass(metaclass=kisa.Class):

            @kisa.static
            def foo(a, b):
                nonlocal foo_called
                foo_called = True
                return 1

            @kisa.static
            def bar(a):
                nonlocal bar_called
                bar_called = True
                return 2

            @kisa.around("foo", "bar")
            def around_tester(method_name, next, *args):
                if method_name == "foo":
                    self.assertEqual(len(args), 2)
                    self.assertEqual(args[0], 1)
                    self.assertEqual(args[1], 'a')
                    return next(*args)
                elif method_name == "bar":
                    self.assertEqual(len(args), 1)
                    self.assertEqual(args[0], 'call')
                    return next(*args)
                else:
                    self.fail(f"Unknown method arround wraps: {method_name}")

        self.assertEqual(StaticClass.foo(1, 'a'), 1)
        self.assertEqual(StaticClass.bar('call'), 2)

        self.assertEqual(foo_called, True)
        self.assertEqual(bar_called, True)

    def test_attr_type_any(self):
        class AnyAttrClass(metaclass=kisa.Class):
            value = kisa.Info(type=any, default=0)

        aac = AnyAttrClass()
        self.assertEqual(aac.value(), 0)
        self.assertEqual(aac.value("T"), "T")
        self.assertEqual(aac.value(), "T")
        self.assertEqual(aac.value(aac), aac)
        self.assertEqual(aac.value(), aac)

    def test_lazy_no_default(self):
        class LazyClass(metaclass=kisa.Class):
            lazy_value = kisa.Info(
                type=int, required=False, allow_none=False, lazy=True)

        lc = LazyClass()
        try:
            lc.lazy_value()
            self.fail("Can't get value of undefined value")
        except AssertionError:
            raise
        except Exception:
            pass

        lc.lazy_value(2)
        self.assertEqual(lc.lazy_value(), 2)
        lc.lazy_value(5)
        self.assertEqual(lc.lazy_value(), 5)

    def test_lazy_no_default_static(self):
        class LazyClassStatic(metaclass=kisa.Class):
            lazy_value = kisa.StaticInfo(type=int, allow_none=False, lazy=True)

        try:
            LazyClassStatic.lazy_value()
            self.fail("Can't get value of undefined value")
        except AssertionError:
            raise
        except Exception:
            pass

        LazyClassStatic.lazy_value(2)
        self.assertEqual(LazyClassStatic.lazy_value(), 2)
        LazyClassStatic.lazy_value(5)
        self.assertEqual(LazyClassStatic.lazy_value(), 5)

    def test_lazy_with_default(self):
        called = False

        def gen_value():
            nonlocal called
            called = True
            return 1

        class LazyClass(metaclass=kisa.Class):
            lazy_value = kisa.Info(type=int, default=gen_value, lazy=True)

        lc = LazyClass()
        self.assertEqual(called, False, "gen_value should be lazy called")
        self.assertEqual(lc.lazy_value(), 1)
        self.assertEqual(called, True, "gen_value should've been called")
        self.assertEqual(lc.lazy_value(2), 2)
        self.assertEqual(lc.lazy_value(), 2)

    def test_lazy_with_default_static(self):
        called = False

        def gen_value():
            nonlocal called
            called = True
            return 1

        class LazyClassStatic(metaclass=kisa.Class):
            lazy_value = kisa.StaticInfo(type=int,
                                         default=gen_value,
                                         allow_none=False,
                                         lazy=True)

        self.assertEqual(called, False, "gen_value should be lazy called")
        self.assertEqual(LazyClassStatic.lazy_value(), 1)
        self.assertEqual(called, True, "gen_value should've been called")
        self.assertEqual(LazyClassStatic.lazy_value(2), 2)
        self.assertEqual(LazyClassStatic.lazy_value(), 2)

    def test_lazy_no_none(self):
        class LazyClass(metaclass=kisa.Class):
            lazy_value = kisa.Info(
                type=int, required=False, allow_none=False, lazy=True)

        lc = LazyClass()
        self.assertEqual(lc.lazy_value(5), 5)
        self.assertEqual(lc.lazy_value(), 5)
        self.assertEqual(lc.lazy_value(6), 6)
        self.assertEqual(lc.lazy_value(), 6)

    def test_lazy_no_none_static(self):
        class LazyClassStatic(metaclass=kisa.Class):
            lazy_value = kisa.StaticInfo(type=int, allow_none=False, lazy=True)

        self.assertEqual(LazyClassStatic.lazy_value(5), 5)
        self.assertEqual(LazyClassStatic.lazy_value(), 5)
        self.assertEqual(LazyClassStatic.lazy_value(6), 6)
        self.assertEqual(LazyClassStatic.lazy_value(), 6)

    def test_modifier_doesnt_exist(self):
        class ModifierClass(metaclass=kisa.Class):
            def foo(self):
                pass

            @kisa.before("foo")
            def bar(self):
                pass

        obj = ModifierClass()

        try:
            obj.bar()
            self.fail(
                "Called attribute modifier even though it's not supposed to exist")
        except AssertionError:
            raise
        except:
            pass

    def test_modifier_doesnt_exist_static(self):
        class ModifierClassStatic(metaclass=kisa.Class):
            @kisa.static
            def foo(self):
                pass

            @kisa.before("foo")
            def bar(self):
                pass

        obj = ModifierClassStatic()

        try:
            ModifierClassStatic.bar()
            self.fail(
                "Called attribute modifier even though it's not supposed to exist")
        except AssertionError:
            raise
        except:
            pass

        try:
            obj.bar()
            self.fail(
                "Called attribute modifier even though it's not supposed to exist")
        except AssertionError:
            raise
        except:
            pass

    def test_default_generated_on_constructor(self):
        class A(metaclass=kisa.Class):
            a = kisa.Info(final=True, default=lambda: 1)
            b = kisa.Info(final=True, default=2)
            c = kisa.Info(final=True, default=3)
            abcde_sum = kisa.Info(final=True, default=lambda self: self.a() +
                                  self.b() +
                                  self.c() +
                                  self.d() +
                                  self.e())
            d = kisa.Info(final=True)
            e = kisa.Info(final=True)

        a = A(d=4, e=5)
        self.assertEqual(a.abcde_sum(), 15)


if __name__ == "__main__":
    unittest.main()
