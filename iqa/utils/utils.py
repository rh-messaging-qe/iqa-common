
class Utils():
    @staticmethod
    def remove_prefix(str, prefix):
        if str.startswith(prefix):
            return str[len(prefix):]
        else:
            return str
