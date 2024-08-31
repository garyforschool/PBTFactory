class MyMap(r.Map):
        default_converters = r.Map.default_converters.copy()
        default_converters["foo"] = r.UnicodeConverter