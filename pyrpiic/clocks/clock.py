import abc


class Clock(abc.ABC):

    @abc.abstractmethod
    def get_frequency(self, **kwargs):
        """ Read frequency from chip. """
        raise NotImplementedError()

    @abc.abstractmethod
    def set_frequency(self, **kwargs):
        """ Write desired frequency to chip. """
        raise NotImplementedError()
