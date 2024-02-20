from abc import ABCMeta, abstractmethod

class AbstractVolume(metaclass=ABCMeta):
    @property
    @abstractmethod
    def bootsector(self) -> str:
        """
        Return boot sector information of the volume
        """
        pass
    