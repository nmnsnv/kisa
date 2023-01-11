
import re
import inspect
import pydoc

from typing import Callable, Dict, List, AbstractSet, MutableSet, Union


class _AbstractMethod(object):
    pass


class _AttributeModifier(object):
    def __init__(self, gen_callback: Callable, name: Union[str, List[str]]):
        self.gen_callback: Callable[[Info], Callable] = gen_callback
        if isinstance(name, str):
            name = [name]
        self.modified_attributes: List[str] = name


class _BeforeClass(_AttributeModifier):
    pass


class _AroundClass(_AttributeModifier):
    pass


class _AfterClass(_AttributeModifier):
    pass


class _StaticClass(object):
    def __init__(self, callback: Callable) -> None:
        self.callback: Callable = callback


class ModifiersList():
    def __init__(self, before=None, around=None, after=None, static=False) -> None:
        if before is None:
            before = []
        if around is None:
            around = []
        if after is None:
            after = []

        self.before: List[_AttributeModifier] = before
        self.around: List[_AttributeModifier] = around
        self.after: List[_AttributeModifier] = after

        self.static: bool = static

    def add_before(self, callback: _AttributeModifier):
        self.before.append(callback)

    def add_around(self, callback: _AttributeModifier):
        self.around.append(callback)

    def add_after(self, callback: _AttributeModifier):
        self.after.append(callback)


class Info(ModifiersList):
    def __init__(self,
                 type=object,
                 required: bool = True,
                 default: any = None,
                 final: bool = False,
                 allow_none: bool = True,
                 lazy: bool = False,
                 before: None = None,
                 around=None,
                 after=None,
                 _static=False,
                 _name=None) -> None:

        super().__init__(before=before, around=around, after=after, static=_static)
        if default is not None or lazy is True:
            self.required: bool = False
        else:
            self.required: bool = required
        self.default = default
        self.final: bool = final
        self.allow_none = allow_none
        self.lazy = lazy
        self._name: str = _name

        self._in_module = self._get_outer_module_name()
        self._current_frame = self._get_outer_frame()
        self._module_frame = self._get_outer_frame().f_back
        self.frame = self._get_outer_frame()

        self._type = type

    def get_type(self, self_name=None, self_value=None):
        if isinstance(self._type, str):
            if self._type == self_name:
                self._type = self_value
            else:
                self._type = self._get_type_from_string(self._type)
        return self._type

    def _get_type_from_string(self, obj_type: str):
        obj = self._search_in_module_scopes(obj_type)

        if obj is None:
            obj = pydoc.locate(obj_type)
            if obj is None or inspect.ismodule(obj):
                obj = pydoc.locate(f"{self._in_module}.{obj_type}")

        if obj is None:
            raise Exception(f"Unknown Type {obj_type}")
        elif inspect.ismodule(obj):
            raise Exception(f"{obj_type} is module: {obj}")
        return obj

    def _search_in_module_scopes(self, obj_type):

        # local frame search
        # NOTE: we dont save .f_locals as a var since it won't be updated.
        #       This is probably caused by a bug in Python 'inspect' library
        # TODO: Search why .f_locals isn't updated if cached (e.g. a=f.f_locals).
        #       It only works when accessed from frame
        match = self.search_in_dict(obj_type, self._module_frame.f_locals)

        if match is None:
            # NOTE: This is probably due to issue with creating classes in __main__.
            #       View https://github.com/python/cpython/issues/100672 for more information
            # global frame search
            match = self.search_in_dict(obj_type,
                                        self._current_frame.f_globals)

        return match

    def search_in_dict(self, obj_type, cur_dict):
        obj_path = obj_type.split(".")

        found = True
        while len(obj_path) > 0:
            cur_obj_module = obj_path.pop()
            if cur_obj_module in cur_dict:
                cur_dict = cur_dict[cur_obj_module]
            else:
                found = False
                break

        if found and not inspect.ismodule(cur_dict):
            return cur_dict
        else:
            return None

    def _get_outer_module_name(self):
        return inspect.getmodulename(self._get_outer_frame().f_code.co_filename)

    def _get_outer_frame(self):
        cur_frame = inspect.currentframe()
        self_filename = cur_frame.f_code.co_filename
        while True:
            cur_filename = cur_frame.f_code.co_filename
            if cur_filename != self_filename:
                return cur_frame
            else:
                cur_frame = cur_frame.f_back


class StaticInfo(Info):
    def __init__(self, type=object, default: any = None, final: bool = False, allow_none=True, lazy: bool = False, before: None = None, around=None, after=None, _name=None) -> None:
        super().__init__(type=type,
                         required=False,
                         default=default,
                         final=final,
                         allow_none=allow_none,
                         lazy=lazy,
                         before=before,
                         around=around,
                         after=after,
                         _static=True,
                         _name=_name)


# TODO: Support non Kisa inheritance
# TODO: Support attribute modifiers for non Kisa inheritance
# TODO: Support for multiple inheritance
# TODO: Fix bug that throws error when calling "super()" from class instance


def _raise(exception: Exception):
    raise exception


class _KisaDict(dict):
    def __init__(self, class_name):
        self.class_name = class_name


class _BasicKisaType(type):
    def __prepare__(class_name, *args, **kwargs):
        val = _KisaDict(class_name)
        return val


class _AbstractEntity(_BasicKisaType):
    @staticmethod
    def abstract_new(cls,
                     clsname,
                     bases,
                     class_desc,
                     is_extandable,
                     is_implemented,
                     extends,
                     implements,
                     kisa_class_type):
        kisa_internal = _KisaInternal(cls=cls,
                                      clsname=clsname,
                                      bases=bases,
                                      kisa_class_type=kisa_class_type,
                                      class_desc=class_desc,
                                      extends=extends,
                                      implements=implements,
                                      is_extandable=is_extandable,
                                      is_implemented=is_implemented)

        _AbstractEntity._disable_abstract_public_constructor(kisa_internal)
        _AbstractEntity._enable_abstract_method(kisa_internal, clsname)

        return kisa_internal

    @staticmethod
    def _enable_abstract_method(kisa_internal, class_name: str):
        abstract_methods: MutableSet[str] = set()

        def unknown_handler(attr_name, attr_val):
            return _AbstractEntity._try_add_abstract_method(abstract_methods, attr_name, attr_val)
        kisa_internal.is_unknown_attribute_type_valid(unknown_handler)

        kisa_internal.on_functions_declared(
            lambda reversed_inheritance: _AbstractEntity._validate_abstract_methods_declared(abstract_methods,
                                                                                             reversed_inheritance,
                                                                                             class_name))

    @staticmethod
    def _disable_abstract_public_constructor(kisa_internal):
        kisa_internal.on_external_constructor_called(
            lambda class_self: _raise(Exception(f"Can't initialize abstract Class \"{class_self.__class__}\"")))

    @staticmethod
    def _try_add_abstract_method(abstract_methods: MutableSet[str], attr_name, attr_value):
        if type(attr_value) is not _AbstractMethod:
            return False

        abstract_methods.add(attr_name)
        return True

    @staticmethod
    def _validate_abstract_methods_declared(all_abstract_func_name: AbstractSet[str],
                                            reversed_inheritance: List,
                                            class_name):
        required_methods = set(all_abstract_func_name)
        has_non_abstract_class = False

        cur_inherited_class: _PrivateClassData
        for cur_inherited_class in reversed_inheritance:
            if cur_inherited_class.kisa_class_type is Class:
                has_non_abstract_class = True

            class_methods = cur_inherited_class.methods_names
            required_methods.difference_update(class_methods)

        if has_non_abstract_class and len(required_methods) > 0:
            raise Exception(
                f"Methods \"{', '.join(required_methods)}\" are not implemented for class \"{reversed_inheritance[0].class_name}\". Required by abstract class \"{class_name}\"")


class AbstractClass(_AbstractEntity):
    def __new__(cls, clsname, bases, class_desc, extends=object, implements=[]):
        kisa_internal = _AbstractEntity.abstract_new(cls=cls,
                                                     clsname=clsname,
                                                     bases=bases,
                                                     class_desc=class_desc,
                                                     kisa_class_type=AbstractClass,
                                                     is_extandable=True,
                                                     is_implemented=False,
                                                     extends=extends,
                                                     implements=implements)

        created_class = kisa_internal.generate()
        return created_class


class Interface(_AbstractEntity):
    def __new__(cls, clsname, bases, class_desc, implements=[]):
        kisa_internal = _AbstractEntity.abstract_new(cls=cls,
                                                     clsname=clsname,
                                                     bases=bases,
                                                     class_desc=class_desc,
                                                     kisa_class_type=AbstractClass,
                                                     is_extandable=False,
                                                     is_implemented=True,
                                                     extends=object,
                                                     implements=implements)

        kisa_internal.enable_regular_attribute_type_checking(
            lambda attr_name, attr_value: isinstance(attr_value, _AbstractMethod))

        created_class = kisa_internal.generate()
        return created_class


class Class(_BasicKisaType):
    def __new__(cls, clsname, bases, class_desc, extends=object, implements=[]):
        kisa_internal = _KisaInternal(cls=cls,
                                      clsname=clsname,
                                      bases=bases,
                                      kisa_class_type=Class,
                                      class_desc=class_desc,
                                      extends=extends,
                                      implements=implements,
                                      is_extandable=True,
                                      is_implemented=False)

        created_class = kisa_internal.generate()
        return created_class


class _PrivateVars():
    def __init__(self) -> None:
        self.private_vars = {}


class _PrivateClassData(_PrivateVars):
    def __init__(self, class_name, kisa_class_type, is_extandable, is_implemented):
        super().__init__()
        self.class_name = class_name
        self.kisa_class_type = kisa_class_type
        self.is_extandable: bool = is_extandable
        self.is_implemented: bool = is_implemented
        self.extends_class = object
        self.implemented_interfaces = []
        self.class_id: int = _KisaInternal.gen_class_id()
        self.internal_constructor: Callable[[any, Dict[str, any]]] = None
        self.methods_names: AbstractSet[Callable] = set()
        self.on_functions_declared: Callable[[
            List[_PrivateClassData]], None] = lambda _: None

        # If the var declais not Info
        self.is_unknown_attribute_type_valid: Callable[[
            str, any], bool] = lambda _attribute_name, _attribute_value: False

        self.is_type_checking_enabled: Callable[[
            str, any], bool] = lambda _attribute_name, _attribute_value: True


class _PrivateObjectData(_PrivateVars):
    def __init__(self):
        super().__init__()


class _KisaInternal():

    # Static
    _static_internal_class_id = 0
    _static_kisa_classes = set()
    _static_classes_data: Dict[any, _PrivateClassData] = {}

    def __init__(self,
                 cls,
                 clsname,
                 class_desc: _KisaDict,
                 extends,
                 implements,
                 bases,
                 is_extandable: bool,  # is created class can be used in extends
                 is_implemented: bool,  # is created class can be used in implements
                 kisa_class_type):

        self._super_name: str = "_super"
        self._obj_private_vars_name: str = "___KISA_PRIVATE__"
        self._attribute_modifiers: List[_AttributeModifier] = []
        self._inherit_attribute_modifiers: dict[str, ModifiersList] = {}
        self._vars_info: Dict[str, Info] = {}
        self._funcs_info: Dict[str, Info] = {}
        self._special_attributes_info: Dict[str, Info] = {}
        self._class_attrs: Dict[str, any] = {}
        self._cls = cls
        self._class_desc: _KisaDict = class_desc
        self._extends = extends
        self._bases: list = list(bases)
        self._private_class_data: _PrivateClassData = _PrivateClassData(kisa_class_type=kisa_class_type,
                                                                        class_name=clsname,
                                                                        is_extandable=is_extandable,
                                                                        is_implemented=is_implemented)
        self._on_external_constructor_called: Callable[[
            any], None] = lambda _: None

        # Ensure implements will be formatted as list or tuple.
        # This enables us to allow the implements format to be as following:
        # * implements=SomeInterface
        # * implements=[SomeInterface]
        # Basically, for a cleaner syntax
        # NOTE: we are not checking if it's iterable since
        #       in the future we'll add support for iterable classes
        if not isinstance(implements, (list, tuple)):
            implements = [implements]

        self._implements: List = implements

    def generate(self):
        # This is to be used in methods
        self._created_class = None

        self._setup_inheritance()

        self._create_special_attributes()

        self._create_super_method()

        self._seperate_vars_and_funcs()

        self._set_attribute_modifiers()

        self._add_vars_to_class()
        self._add_methods_to_class()
        self._add_special_attributes_to_class()

        self._created_class = type(self._private_class_data.class_name,
                                   tuple(self._bases),
                                   self._class_attrs)

        self._handle_class_created()

        return self._created_class

    def _add_special_attributes_to_class(self):
        for special_attr in self._special_attributes_info.keys():
            info = self._special_attributes_info[special_attr]
            self._class_attrs[special_attr] = self._gen_class_method(special_attr,
                                                                     info.default,
                                                                     info)

    def _add_methods_to_class(self):
        for func_name in self._funcs_info.keys():
            info = self._funcs_info[func_name]
            self._class_attrs[func_name] = self._gen_class_method(func_name,
                                                                  info.default,
                                                                  info)

    def _add_vars_to_class(self):
        for var_name in self._vars_info.keys():
            info = self._vars_info[var_name]
            if info.final:
                info.add_around(self._gen_around_final_attr(var_name))

            self._class_attrs[var_name] = self._gen_class_method(var_name,
                                                                 self._gen_attribute_get_set(
                                                                     var_name),
                                                                 info)

    def _gen_around_final_attr(self, var_name):
        was_called = False
        is_static = self._vars_info[var_name].static

        def inner(*args, **kwargs):
            args = [*args]

            if not is_static:
                args.pop(0)

            attr_name = args.pop(0)
            next = args.pop(0)

            nonlocal was_called
            if len(args) == 0:
                # getter, resume as usual
                return next(*args, **kwargs)
            else:
                # Setter, only allow to be called once
                if was_called:
                    raise Exception(
                        f"Tried to modify a final attribute \"{var_name}\"")
                else:
                    was_called = True
                    return next(*args, **kwargs)
        return inner

    def _create_special_attributes(self):
        clsname = self._private_class_data.class_name
        special_attributes = {}
        special_attributes['__init__'] = self._gen_class_constructor(clsname)
        special_attributes['__setattr__'] = self._gen_class_setter()
        special_attributes['__getattribute__'] = self._gen_class_getter()
        special_attributes['__new__'] = self._gen_class_new_method()

        for special_attr in special_attributes.keys():
            self._special_attributes_info[special_attr] = Info(required=False,
                                                               default=special_attributes[special_attr],
                                                               final=False,
                                                               _name=special_attr)
        # self._special_attributes['__class__'] = Class
        # self._special_attributes['__classcell__'] = class_desc['__classcell__']

    def _gen_class_new_method(self):
        def inner(cls, *args, **kwargs):
            extends_class = self._private_class_data.extends_class
            # TODO: Remove this trick that relies passes object no args
            if extends_class is object:
                return extends_class.__new__(cls)
            else:
                return extends_class.__new__(cls, *args, **kwargs)
        return inner

    def _handle_class_created(self):
        _KisaInternal._add_class_kisa(self._created_class)
        _KisaInternal._static_classes_data[self._created_class] = self._private_class_data

        self._setup_static_attributes()

    def _setup_static_attributes(self):
        for var_name in self._vars_info.keys():
            var_info = self._vars_info[var_name]
            if not var_info.static:
                continue

            if not var_info.lazy:
                # Assign class static vars
                static_var_default_value = self._get_default_value(var_name,
                                                                   class_self=self._created_class)

                getattr(self._created_class,
                        var_name)(static_var_default_value)

    def on_external_constructor_called(self, callback: Callable[[], None]):
        self._on_external_constructor_called = callback

    def on_functions_declared(self, callback: Callable[[List[_PrivateClassData]], None]):
        self._private_class_data.on_functions_declared = callback

    def is_unknown_attribute_type_valid(self, callback: Callable[[str, any], bool]):
        self._private_class_data.is_unknown_attribute_type_valid = callback

    def enable_regular_attribute_type_checking(self, callback: Callable[[str, any], bool]):
        self._private_class_data.is_type_checking_enabled = callback

    def _set_attribute_modifiers(self):
        class_desc = self._class_desc

        for attr_name in class_desc:
            var_value = class_desc[attr_name]
            if not isinstance(var_value, _AttributeModifier):
                # For now save the modifiers until after self._vars_info created, then insert them there
                continue
            cur_attribute_modifier: _AttributeModifier = var_value

            for name in cur_attribute_modifier.modified_attributes:
                if name in self._vars_info:
                    required_table = self._vars_info
                elif name in self._funcs_info:
                    required_table = self._funcs_info
                elif name in self._special_attributes_info:
                    required_table = self._special_attributes_info
                # TODO: validate attribute exists in father
                elif _KisaInternal._is_class_kisa(self._private_class_data.extends_class):
                    if not name in self._inherit_attribute_modifiers:
                        self._inherit_attribute_modifiers[name] = ModifiersList(
                        )
                    required_table = self._inherit_attribute_modifiers
                else:
                    raise Exception(
                        f"Cannot put Attribute Modifier for unknown Attribute \"{name}\"")

                required_info = required_table[name]

                if type(cur_attribute_modifier) is _BeforeClass:
                    required_list = required_info.before
                elif type(cur_attribute_modifier) is _AroundClass:
                    required_list = required_info.around
                elif type(cur_attribute_modifier) is _AfterClass:
                    required_list = required_info.after
                else:
                    raise Exception(
                        f"Unknown modifier type for \"{name}\"")

                callback = cur_attribute_modifier.gen_callback(required_info)
                required_list.append(callback)

        for inherit_modifier in self._inherit_attribute_modifiers.keys():
            info = self._inherit_attribute_modifiers[inherit_modifier]
            self._class_attrs[inherit_modifier] = self._gen_class_method(inherit_modifier,
                                                                         self._gen_inherite_attribute_call(
                                                                             inherit_modifier),
                                                                         info)

    def _seperate_vars_and_funcs(self):
        class_desc = self._class_desc

        for attr_name in class_desc:
            # NOTE: Don't allow python special methods to be modified unless we support them
            # TODO: theoretically, there shouldn't be a problem to override these.
            #       check and remove if found unnecessary
            if re.match("^__.+__$", attr_name) and attr_name not in self._special_attributes_info:
                # Python unmodified special attributes, skip!
                continue

            attr_value = class_desc[attr_name]
            if not self._private_class_data.is_type_checking_enabled(attr_name, attr_value):
                raise Exception(
                    f"attribute \"{attr_name}\" cant have value: \"{attr_value}\" for {self._private_class_data.class_name}")

            if callable(attr_value):
                self._funcs_info[attr_name] = Info(required=False,
                                                   default=attr_value,
                                                   final=True,
                                                   _name=attr_name)
            elif isinstance(attr_value, Info):
                attr_value._name = attr_name
                self._vars_info[attr_name] = attr_value
            elif isinstance(attr_value, _AttributeModifier):
                continue
            elif isinstance(attr_value, _StaticClass):
                self._funcs_info[attr_name] = Info(required=False,
                                                   default=attr_value.callback,
                                                   final=True,
                                                   _static=True,
                                                   _name=attr_name)
            elif not self._private_class_data.is_unknown_attribute_type_valid(attr_name, attr_value):
                raise Exception(
                    f"attribute \"{attr_name}\" cant have value: \"{attr_value}\"")

        self._private_class_data.methods_names = set(self._funcs_info.keys())
        self._trigger_functions_declared()

    def _trigger_functions_declared(self):
        def inner(cur_class_data: _PrivateClassData, reversed_inheritance: List[_PrivateClassData]):
            cur_class_data.on_functions_declared(reversed_inheritance)
            for father_class in [cur_class_data.extends_class, *cur_class_data.implemented_interfaces]:
                if father_class not in _KisaInternal._static_classes_data:
                    # Got out of Kisa inheritance
                    continue
                father_class_data = _KisaInternal._get_class_private_data(
                    father_class)
                inner(father_class_data, [
                      *reversed_inheritance, cur_class_data])

        inner(self._private_class_data, [])

    def _create_super_method(self):
        self._funcs_info[self._super_name] = Info(required=False,
                                                  default=self._get_super,
                                                  final=True,
                                                  _name=self._super_name)

    def _gen_class_constructor(self, clsname):
        def internal_constructor(class_self, user_attributes_map):
            super_args = {}
            for given_var in user_attributes_map.keys():
                if given_var not in self._vars_info:
                    super_args[given_var] = user_attributes_map[given_var]

            if _KisaInternal._is_class_kisa(self._private_class_data.extends_class):

                _KisaInternal \
                    ._get_class_private_data(self._private_class_data.extends_class) \
                    .internal_constructor(class_self, super_args)
            else:
                super(self._created_class, class_self).__init__(**super_args)

            default_attributes = []

            for required_var in self._vars_info.keys():
                if self._vars_info[required_var].static:
                    continue
                elif required_var in user_attributes_map:
                    var_value = user_attributes_map[required_var]
                elif self._vars_info[required_var].required:
                    raise Exception(
                        f"\"{required_var}\" is Missing in instance creation for class {clsname}")
                elif self._vars_info[required_var].lazy:
                    continue
                else:
                    default_attributes.append(required_var)
                    continue

                # Set default value via setter
                getattr(class_self, required_var)(var_value)

            for default_var in default_attributes:
                if default_var in self._get_private_vars(class_self).private_vars:
                    # Already was initialized (through the lazy mechanism)
                    continue

                var_value = self._get_default_value(default_var,
                                                    class_self=class_self)
                # Set default value via setter
                getattr(class_self, default_var)(var_value)

        self._private_class_data.internal_constructor = internal_constructor

        def class_constructor(class_self, **kwargs):
            # NOTE: We create this since it's required in here as well
            self._create_private_vars(class_self)

            self._on_external_constructor_called(class_self)
            self._private_class_data.internal_constructor(class_self=class_self,
                                                          user_attributes_map=kwargs)

        return class_constructor

    def _get_default_value(self, required_var: str, class_self):
        if callable(self._vars_info[required_var].default):
            args = []

            default_method: Callable = self._vars_info[required_var].default
            default_args = inspect.getfullargspec(default_method)
            default_require_self = len(default_args.args) > 0 or \
                default_args.varargs is not None

            if default_require_self:
                args.append(class_self)

            var_value = default_method(*args)
        else:
            var_value = self._vars_info[required_var].default
        return var_value

    def _gen_class_getter(self):
        def class_getter(class_self, key):
            return super(self._created_class, class_self).__getattribute__(key)

        return class_getter

    def _gen_class_setter(self):
        def class_setter(class_self, key: str, val):
            if key not in self._vars_info and key not in self.all_funcs_info:
                raise Exception(f"Unknown attribute \"{key}\"")
            else:
                raise Exception(
                    f"Can't modify instance values: Tried to modify \"{key}\"")

        return class_setter

    def _gen_attribute_get_set(self, var_name):
        is_static = self._vars_info[var_name].static
        allow_none = self._vars_info[var_name].allow_none
        is_lazy = self._vars_info[var_name].lazy

        def inner(*args):
            args = [*args]
            if is_static:
                class_self = self._created_class
                private_vars_table: _PrivateVars = self._private_class_data
            else:
                class_self = args.pop(0)
                private_vars_table: _PrivateVars = self._get_private_vars(
                    class_self)

            if len(args) == 0:
                # get value
                if var_name not in private_vars_table.private_vars and var_name in self._vars_info:
                    var_value = self._get_default_value(var_name,
                                                        class_self=class_self)

                    # Set default value via setter
                    getattr(class_self, var_name)(var_value)

                return private_vars_table.private_vars[var_name]
            else:
                # set value
                val = args[0]

                var_type = self._vars_info[var_name].get_type()
                if var_type is any:
                    is_valid_type = True
                else:
                    try:
                        is_valid_type = isinstance(val, var_type)
                    except Exception as e:
                        raise Exception(
                            f"An error when comparing types: \"{var_name}\" to class \"{var_type}\" :: {e}")

                if not is_valid_type:
                    if not (allow_none and val is None):
                        raise Exception(
                            f"\"{var_name}\" must be of type: {var_type}")
                private_vars_table.private_vars[var_name] = val
                return val

        return inner

    def _gen_inherite_attribute_call(self, attribute_name):
        def inner(class_self, *args, **kwargs):
            attribute = getattr(
                super(self._created_class, class_self), attribute_name)
            return attribute(*args, **kwargs)
        return inner

    def _gen_class_method(self, method_name, callback, method_info: ModifiersList):
        def inner(*args, **kwargs):
            args = [*args]
            class_self = None
            if not method_info.static:
                class_self = args.pop(0)

            def get_args_list(input_self, *input_args):
                if method_info.static:
                    return input_args
                else:
                    return [input_self, *input_args]

            def gen_around(callback, around_next):
                def around_inner(*inner_args, **inner_kwargs):
                    return callback(*get_args_list(class_self, method_name, around_next, *inner_args),
                                    **inner_kwargs)
                return around_inner

            for before_callback in method_info.before:
                before_callback(*get_args_list(class_self,
                                               method_name, *args), **kwargs)

            def final_next_call(*around_next_args, **around_next_kwargs):
                return callback(*get_args_list(class_self, *around_next_args),
                                **around_next_kwargs)

            around_next = final_next_call

            for around_callback in method_info.around:
                around_next = gen_around(around_callback, around_next)
            retval = around_next(*args, **kwargs)

            for after_callback in method_info.after:
                after_callback(*get_args_list(class_self,
                                              method_name, *args), **kwargs)

            return retval

        if method_info.static:
            return staticmethod(lambda *args, **kwargs: inner(*args, **kwargs))
        else:
            return inner

    def _create_private_vars(self, class_self):
        if not hasattr(class_self, self._obj_private_vars_name):
            private_vars = _PrivateObjectData()
            vars(class_self)[self._obj_private_vars_name] = private_vars

    def _get_private_vars(self, class_self) -> _PrivateObjectData:
        return getattr(class_self, self._obj_private_vars_name)

    def _get_super(self, class_self):
        return super(self._created_class, class_self)

    def _setup_inheritance(self):
        if self._bases:
            raise Exception(
                f"Python builtin inheritance is not supported, use extends/implements instead")

        self._private_class_data.extends_class = self._extends
        self._private_class_data.implemented_interfaces = self._implements

        extends_class = self._private_class_data.extends_class

        if _KisaInternal._can_class_be_extended(extends_class) is False:
            raise Exception(
                f"Can't extend {extends_class}")

        for to_implement_class in self._private_class_data.implemented_interfaces:
            if _KisaInternal._can_class_be_implemented(to_implement_class) is False:
                raise Exception(
                    f"Can't implement {to_implement_class}")

        # Currently, we dont add interfaces to Python inheritance tree
        self._bases.append(extends_class)

    @staticmethod
    def _can_class_be_extended(extends_class):
        # Value for non-Kisa classes, currently for object only
        is_extandable = True
        if extends_class in _KisaInternal._static_classes_data:
            is_extandable = _KisaInternal._get_class_private_data(
                extends_class).is_extandable

        return is_extandable

    @staticmethod
    def _can_class_be_implemented(to_implement_class):
        # Value for non-Kisa classes implemented, currently for object only
        is_implemented = False
        if to_implement_class in _KisaInternal._static_classes_data:
            is_implemented = _KisaInternal._get_class_private_data(
                to_implement_class).is_implemented

        return is_implemented

    @staticmethod
    def gen_class_id():
        _KisaInternal._static_internal_class_id += 1
        return _KisaInternal._static_internal_class_id

    @staticmethod
    def _is_class_kisa(cls):
        return cls in _KisaInternal._static_kisa_classes

    @staticmethod
    def _is_instance_kisa(instance):
        return _KisaInternal._is_class_kisa(instance.__class__)

    @staticmethod
    def _add_class_kisa(cls):
        _KisaInternal._static_kisa_classes.add(cls)

    @staticmethod
    def _get_class_private_data(kisa_class):
        return _KisaInternal._static_classes_data[kisa_class]


def before(*attribute_name):
    return lambda callback: _BeforeClass(gen_callback=lambda *args: callback, name=attribute_name)


def around(*attribute_name):
    return lambda callback: _AroundClass(gen_callback=lambda *args: callback, name=attribute_name)


def after(*attribute_name):
    return lambda callback: _AfterClass(gen_callback=lambda *args: callback, name=attribute_name)


def abstract(_callback):
    return _AbstractMethod()


def static(callback: Callable):
    return _StaticClass(callback)

# TODO: add validation of getter return type


def getter(attribute_name):
    def inner(callback):
        def generate_getter(info: Info):
            def generic_around_getter(*args, **kwargs):
                args = [*args]
                callback_args = []
                if not info.static:
                    # Called as object
                    obj_self = callback_args.append(args.pop(0))

                attr_name = args.pop(0)
                next = args.pop(0)

                if len(args) > 0 or len(kwargs) > 0:
                    return next(*args, **kwargs)
                else:
                    # Get value
                    attr_val = next(*args, **kwargs)
                    callback_args.append(attr_val)
                    return callback(*callback_args)

            return generic_around_getter
        return _AroundClass(gen_callback=generate_getter, name=attribute_name)

    return inner


def setter(attribute_name):
    def inner(callback):
        def generate_setter(info: Info):
            def generic_around_setter(*args, **kwargs):
                args = [*args]
                callback_args = []
                if not info.static:
                    # Called as object
                    obj_self = callback_args.append(args.pop(0))

                attr_name = args.pop(0)
                next = args.pop(0)

                if len(args) != 1 or len(kwargs) > 0:
                    return next(*args, **kwargs)
                else:
                    # Set value:
                    new_value = args.pop(0)
                    callback_args.append(new_value)
                    # new_set_value = callback(obj_self, new_value)
                    new_set_value = callback(*callback_args)
                    return next(new_set_value)

            return generic_around_setter
        return _AroundClass(gen_callback=generate_setter, name=attribute_name)

    return inner
